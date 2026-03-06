from __future__ import annotations

import importlib
import sys
import tomllib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from bub.skills import _read_skill

REPO_ROOT = Path(__file__).resolve().parents[1]
BUBSEEK_ROOT = REPO_ROOT
BUBSEEK_SRC = BUBSEEK_ROOT / "src"


@contextmanager
def imported_bubseek_modules(*module_names: str) -> Iterator[list[object]]:
    sys.path.insert(0, str(BUBSEEK_SRC))
    try:
        yield [importlib.import_module(name) for name in module_names]
    finally:
        sys.path.remove(str(BUBSEEK_SRC))
        for module_name in list(sys.modules):
            if module_name == "bubseek" or module_name.startswith("bubseek."):
                sys.modules.pop(module_name, None)


def test_bubseek_pyproject_depends_on_bub() -> None:
    data = tomllib.loads((BUBSEEK_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = data["project"]["dependencies"]

    assert isinstance(dependencies, list)
    assert any(item.startswith("bub @ git+https://github.com/bubbuild/bub.git@") for item in dependencies)
    assert "python-dotenv>=1.0.0" in dependencies
    assert "pydantic>=2.0.0" in dependencies
    assert "pydantic-settings>=2.0.0" in dependencies
    assert "typer>=0.9.0" in dependencies


def test_bubseek_config_loader_returns_default_packages() -> None:
    with imported_bubseek_modules("bubseek") as [bubseek]:
        packages = bubseek.default_contrib_packages()
        skills = bubseek.bundled_skill_names()
        config = bubseek.load_config(BUBSEEK_ROOT / "bubseek.toml")

    assert packages == ["bub-schedule"]
    assert skills == ["bubseek-bootstrap"]
    assert config["project"]["name"] == "bubseek"
    assert config["bub"]["repo"] == "https://github.com/bubbuild/bub"
    assert config["bub"]["ref"] == "frost/bub-framework"


def test_bubseek_bundled_skill_has_valid_frontmatter() -> None:
    skill_dir = BUBSEEK_ROOT / "skills" / "bubseek-bootstrap"
    metadata = _read_skill(skill_dir, source="builtin")

    assert metadata is not None
    assert metadata.name == "bubseek-bootstrap"


def test_bubseek_skills_directory_has_readme() -> None:
    readme_path = BUBSEEK_ROOT / "skills" / "README.md"

    assert readme_path.is_file()
    assert "bundled" in readme_path.read_text(encoding="utf-8").lower()


def test_bubseek_can_install_skills_to_workspace(tmp_path: Path) -> None:
    with imported_bubseek_modules("bubseek") as [bubseek]:
        installed = bubseek.install_skills_to_workspace(tmp_path)

    target = tmp_path / ".agents" / "skills" / "bubseek-bootstrap" / "SKILL.md"
    assert target.exists()
    assert installed == [target]


def test_bubseek_can_generate_lock_from_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dist_root = tmp_path
    skills_dir = tmp_path / "skills" / "demo-skill"
    skills_dir.mkdir(parents=True)
    (skills_dir / "SKILL.md").write_text("---\nname: demo-skill\ndescription: demo\n---\nBody\n", encoding="utf-8")
    runtime_bub = dist_root / "runtime" / "bub"
    runtime_bub.mkdir(parents=True)
    (runtime_bub / "pyproject.toml").write_text("[project]\nname='bub'\nversion='0.3.0'\n", encoding="utf-8")
    (runtime_bub / "README.md").write_text("demo", encoding="utf-8")
    config_path = tmp_path / "bubseek.toml"
    config_path.write_text(
        "\n".join([
            "[project]",
            'name = "demo"',
            'version = "0.0.1"',
            "",
            "[bub]",
            'path = "runtime/bub"',
            "",
            "[[contrib]]",
            'name = "bub-codex"',
            'repo = "https://github.com/bubbuild/bub-contrib"',
            'path = "packages/bub-codex"',
            'ref = "main"',
            "",
            "[[skills]]",
            'name = "demo-skill"',
            'path = "skills/demo-skill"',
            "",
            "[[skills]]",
            'name = "remote-skill"',
            'repo = "https://github.com/example/skill-repo"',
            'path = "skills/remote-skill"',
            'ref = "v1.2.3"',
            "",
        ]),
        encoding="utf-8",
    )

    with imported_bubseek_modules("bubseek.config") as [config_mod]:
        monkeypatch.setattr(
            config_mod,
            "_resolve_git_ref",
            lambda **kwargs: {
                ("https://github.com/bubbuild/bub-contrib.git", "main"): "a" * 40,
                ("https://github.com/example/skill-repo.git", "v1.2.3"): "b" * 40,
            }[(kwargs["repo"], kwargs["ref"])],
        )
        lock_path = config_mod.generate_lock(config_path=config_path)

    lock_data = tomllib.loads(lock_path.read_text(encoding="utf-8"))
    assert lock_data["meta"]["lock_version"] == 1
    assert lock_data["bub"]["kind"] == "local"
    assert lock_data["bub"]["path"] == "runtime/bub"
    assert lock_data["contrib"][0]["name"] == "bub-codex"
    assert lock_data["contrib"][0]["kind"] == "remote"
    assert lock_data["skills"][0]["name"] == "demo-skill"
    assert lock_data["skills"][0]["kind"] == "local"
    assert lock_data["skills"][0]["path"] == "skills/demo-skill"
    assert lock_data["skills"][1]["name"] == "remote-skill"
    assert lock_data["skills"][1]["kind"] == "remote"
    assert lock_data["contrib"][0]["resolved_commit"] == "a" * 40
    assert lock_data["skills"][1]["resolved_commit"] == "b" * 40
    assert (
        lock_data["contrib"][0]["source"]
        == f"git+https://github.com/bubbuild/bub-contrib.git@{'a' * 40}#subdirectory=packages/bub-codex"
    )
    assert (
        lock_data["skills"][1]["source"]
        == f"git+https://github.com/example/skill-repo.git@{'b' * 40}#subdirectory=skills/remote-skill"
    )


def test_bubseek_wrapper_forwards_non_management_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    with imported_bubseek_modules("bubseek.__main__") as [main_mod]:
        observed: dict[str, object] = {}

        def _forward(args: list[str]) -> int:
            observed["args"] = args
            return 0

        monkeypatch.setattr(
            main_mod,
            "_default_dependencies",
            lambda: main_mod.BubseekCliDependencies(
                generate_config=main_mod.generate_config,
                generate_lock=main_mod.generate_lock,
                sync_from_lock=main_mod.sync_from_lock,
                forward_command=_forward,
                echo=lambda message: None,
            ),
        )
        result = main_mod.main(["chat", "--help"])

    assert result == 0
    assert observed["args"] == ["chat", "--help"]


def test_bubseek_wrapper_forwards_help_command(monkeypatch: pytest.MonkeyPatch) -> None:
    with imported_bubseek_modules("bubseek.__main__") as [main_mod]:
        observed: dict[str, object] = {}

        def _forward(args: list[str]) -> int:
            observed["args"] = args
            return 0

        monkeypatch.setattr(
            main_mod,
            "_default_dependencies",
            lambda: main_mod.BubseekCliDependencies(
                generate_config=main_mod.generate_config,
                generate_lock=main_mod.generate_lock,
                sync_from_lock=main_mod.sync_from_lock,
                forward_command=_forward,
                echo=lambda message: None,
            ),
        )
        result = main_mod.main(["help"])

    assert result == 0
    assert observed["args"] == ["help"]


def test_bubseek_wrapper_forwards_dotenv_values(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join([
            "bub_api_key=demo-key",
            "openrouter_base_url=https://openrouter.ai/api/v1",
        ]),
        encoding="utf-8",
    )

    with imported_bubseek_modules("bubseek.__main__") as [main_mod]:
        observed: dict[str, object] = {}

        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(main_mod.shutil, "which", lambda _name: "/usr/bin/bub")

        def _capture_run(command: list[str], *, check: bool, env: dict[str, str]) -> SimpleNamespace:
            observed["command"] = command
            observed["env"] = env
            return SimpleNamespace(returncode=0)

        monkeypatch.setattr(main_mod.subprocess, "run", _capture_run)
        result = main_mod._forward_to_bub(["chat"])

    assert result == 0
    assert observed["command"] == ["/usr/bin/bub", "chat"]
    assert observed["env"]["bub_api_key"] == "demo-key"
    assert observed["env"]["openrouter_base_url"] == "https://openrouter.ai/api/v1"


def test_bubseek_wrapper_help_mentions_core_management_commands() -> None:
    runner = CliRunner()
    with imported_bubseek_modules("bubseek.__main__") as [main_mod]:
        result = runner.invoke(main_mod.app, ["--help"])

    assert result.exit_code == 0
    assert "init" in result.stdout
    assert "lock" in result.stdout
    assert "sync" in result.stdout
    assert "install-skills" not in result.stdout


def test_bubseek_sync_installs_local_skill_from_lock(tmp_path: Path) -> None:
    dist_root = tmp_path / "dist"
    workspace = tmp_path / "workspace"
    skill_dir = dist_root / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: demo-skill\ndescription: demo\n---\nBody\n", encoding="utf-8")

    config_path = dist_root / "bubseek.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("[project]\nname='demo'\nversion='0.0.1'\n", encoding="utf-8")

    with imported_bubseek_modules("bubseek.config", "bubseek.sync") as [config_mod, sync_mod]:
        lock_path = dist_root / "bubseek.lock"
        lock_path.write_text(
            "\n".join([
                "[meta]",
                "lock_version = 1",
                'config_file = "bubseek.toml"',
                f'config_sha256 = "{config_mod.sha256_file(config_path)}"',
                "",
                "[[skills]]",
                'name = "demo-skill"',
                'kind = "local"',
                'path = "skills/demo-skill"',
                f'sha256 = "{config_mod.sha256_dir(skill_dir)}"',
                "",
            ]),
            encoding="utf-8",
        )
        result = sync_mod.sync_from_lock(
            config_path=config_path,
            lock_path=lock_path,
            workspace=workspace,
            sync_contrib=False,
            sync_skills=True,
            overwrite_skills=False,
        )

    target = workspace / ".agents" / "skills" / "demo-skill" / "SKILL.md"
    assert target.exists()
    assert result.installed_bub is None
    assert result.installed_contrib == []
    assert result.skipped_skills == []
    assert result.installed_skills == [target]


def test_bubseek_sync_rejects_local_skill_checksum_mismatch(tmp_path: Path) -> None:
    dist_root = tmp_path / "dist"
    workspace = tmp_path / "workspace"
    skill_dir = dist_root / "skills" / "demo-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("---\nname: demo-skill\ndescription: demo\n---\nBody\n", encoding="utf-8")

    config_path = dist_root / "bubseek.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("[project]\nname='demo'\nversion='0.0.1'\n", encoding="utf-8")

    lock_path = dist_root / "bubseek.lock"
    with imported_bubseek_modules("bubseek.config", "bubseek.sync") as [config_mod, sync_mod]:
        lock_path.write_text(
            "\n".join([
                "[meta]",
                "lock_version = 1",
                'config_file = "bubseek.toml"',
                f'config_sha256 = "{config_mod.sha256_file(config_path)}"',
                "",
                "[[skills]]",
                'name = "demo-skill"',
                'kind = "local"',
                'path = "skills/demo-skill"',
                'sha256 = "bad-checksum"',
                "",
            ]),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="local skill checksum mismatch"):
            sync_mod.sync_from_lock(
                config_path=config_path,
                lock_path=lock_path,
                workspace=workspace,
                sync_contrib=False,
                sync_skills=True,
            )


def test_bubseek_sync_rejects_lock_config_checksum_mismatch(tmp_path: Path) -> None:
    dist_root = tmp_path / "dist"
    config_path = dist_root / "bubseek.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("[project]\nname='demo'\nversion='0.0.1'\n", encoding="utf-8")
    lock_path = dist_root / "bubseek.lock"
    lock_path.write_text(
        "\n".join([
            "[meta]",
            "lock_version = 1",
            'config_file = "bubseek.toml"',
            'config_sha256 = "bad-checksum"',
            "",
        ]),
        encoding="utf-8",
    )

    with (
        imported_bubseek_modules("bubseek.sync") as [sync_mod],
        pytest.raises(ValueError, match="lock config checksum mismatch"),
    ):
        sync_mod.sync_from_lock(
            config_path=config_path,
            lock_path=lock_path,
            workspace=tmp_path / "workspace",
            sync_contrib=False,
            sync_skills=False,
        )


def test_bubseek_sync_installs_bub_before_contrib(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dist_root = tmp_path / "dist"
    config_path = dist_root / "bubseek.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("[project]\nname='demo'\nversion='0.0.1'\n", encoding="utf-8")

    runtime_bub = dist_root / "runtime" / "bub"
    runtime_bub.mkdir(parents=True)
    (runtime_bub / "pyproject.toml").write_text("[project]\nname='bub'\nversion='0.3.0'\n", encoding="utf-8")
    (runtime_bub / "README.md").write_text("demo", encoding="utf-8")

    contrib_source = f"git+https://github.com/example/contrib.git@{'a' * 40}#subdirectory=packages/bub-codex"
    cache_root = tmp_path / "cache"
    checkout_dir = cache_root / "git" / "checkout"
    package_dir = checkout_dir / "packages" / "bub-codex"
    package_dir.mkdir(parents=True)
    (package_dir / "pyproject.toml").write_text("[project]\nname='bub-codex'\nversion='0.0.1'\n", encoding="utf-8")

    lock_path = dist_root / "bubseek.lock"
    with imported_bubseek_modules("bubseek.config", "bubseek.sync") as [config_mod, sync_mod]:
        lock_path.write_text(
            "\n".join([
                "[meta]",
                "lock_version = 1",
                'config_file = "bubseek.toml"',
                f'config_sha256 = "{config_mod.sha256_file(config_path)}"',
                "",
                "[bub]",
                'kind = "local"',
                f'path = "{runtime_bub.relative_to(dist_root).as_posix()}"',
                f'sha256 = "{config_mod.sha256_package_dir(runtime_bub)}"',
                "",
                "[[contrib]]",
                'name = "bub-codex"',
                'kind = "remote"',
                f'source = "{contrib_source}"',
                f'sha256 = "{config_mod.sha256_text(contrib_source)}"',
                f'resolved_commit = "{"a" * 40}"',
                "",
            ]),
            encoding="utf-8",
        )

        monkeypatch.setenv(sync_mod.CACHE_DIR_ENV, str(cache_root))
        monkeypatch.setattr(
            sync_mod, "_resolve_cached_source_target", lambda source, source_kind: package_dir.resolve()
        )

        observed: dict[str, object] = {}

        def _capture_command(command: list[str]) -> None:
            observed["command"] = command

        monkeypatch.setattr(sync_mod, "_run_command", _capture_command)
        result = sync_mod.sync_from_lock(
            config_path=config_path,
            lock_path=lock_path,
            workspace=tmp_path / "workspace",
            sync_contrib=True,
            sync_skills=False,
        )

    assert observed["command"] == [
        "uv",
        "pip",
        "install",
        "--no-sources",
        str(runtime_bub.resolve()),
        str(package_dir.resolve()),
    ]
    assert result.installed_bub == str(runtime_bub.resolve())
    assert result.installed_contrib == ["bub-codex"]


def test_remote_lock_rejects_mismatched_resolved_commit(tmp_path: Path) -> None:
    lock_path = tmp_path / "bubseek.lock"
    lock_path.write_text(
        "\n".join([
            "[meta]",
            "lock_version = 1",
            'config_file = "bubseek.toml"',
            'config_sha256 = "dummy"',
            "",
            "[[contrib]]",
            'name = "bub-codex"',
            'kind = "remote"',
            f'source = "git+https://github.com/example/contrib.git@{"a" * 40}#subdirectory=packages/bub-codex"',
            'sha256 = "dummy"',
            f'resolved_commit = "{"b" * 40}"',
            "",
        ]),
        encoding="utf-8",
    )

    with (
        imported_bubseek_modules("bubseek.config") as [config_mod],
        pytest.raises(ValueError, match="source ref does not match resolved_commit"),
    ):
        config_mod.load_lock(lock_path)


def test_remote_skill_dir_uses_cache_without_recloning(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with imported_bubseek_modules("bubseek.config", "bubseek.sync") as [config_mod, sync_mod]:
        source = "git+https://github.com/example/skills.git@main#subdirectory=skills/remote-skill"
        entry = config_mod.LockedSkillEntry(
            name="remote-skill",
            kind="remote",
            source=source,
            sha256=config_mod.sha256_text(source),
        )
        cache_root = tmp_path / "cache"
        monkeypatch.setenv(sync_mod.CACHE_DIR_ENV, str(cache_root))
        repo, ref, _ = sync_mod._parse_git_source(source)
        checkout_dir = cache_root / "git" / sync_mod._cache_key(repo=repo, ref=ref)
        skill_dir = checkout_dir / "skills" / "remote-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("---\nname: remote-skill\ndescription: demo\n---\nBody\n", encoding="utf-8")
        (checkout_dir / sync_mod.CACHE_KEY_FILE).write_text(
            sync_mod._cache_marker(repo=repo, ref=ref), encoding="utf-8"
        )

        def _fail_clone(**kwargs: object) -> None:
            raise AssertionError("cache reuse should not clone again")

        monkeypatch.setattr(sync_mod, "_clone_repo", _fail_clone)
        with sync_mod._remote_skill_dir(entry) as source_dir:
            assert source_dir == skill_dir.resolve()


def test_install_contrib_entries_uses_shared_checkout_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with imported_bubseek_modules("bubseek.config", "bubseek.sync") as [config_mod, sync_mod]:
        source = "git+https://github.com/example/contrib.git@main#subdirectory=packages/bub-codex"
        entry = config_mod.LockedContribEntry(
            name="bub-codex",
            kind="remote",
            source=source,
            sha256=config_mod.sha256_text(source),
        )
        cache_root = tmp_path / "cache"
        monkeypatch.setenv(sync_mod.CACHE_DIR_ENV, str(cache_root))
        repo, ref, _ = sync_mod._parse_git_source(source)
        checkout_dir = cache_root / "git" / sync_mod._cache_key(repo=repo, ref=ref)
        package_dir = checkout_dir / "packages" / "bub-codex"
        package_dir.mkdir(parents=True)
        (package_dir / "pyproject.toml").write_text("[project]\nname='bub-codex'\nversion='0.0.1'\n", encoding="utf-8")
        (checkout_dir / sync_mod.CACHE_KEY_FILE).write_text(
            sync_mod._cache_marker(repo=repo, ref=ref), encoding="utf-8"
        )

        observed: dict[str, object] = {}

        def _fail_clone(**kwargs: object) -> None:
            raise AssertionError("shared cache should avoid recloning")

        def _capture_command(command: list[str]) -> None:
            observed["command"] = command

        monkeypatch.setattr(sync_mod, "_clone_repo", _fail_clone)
        monkeypatch.setattr(sync_mod, "_run_command", _capture_command)
        installed_bub, installed_contrib = sync_mod._install_distribution_packages(
            bub_entry=None,
            contrib_entries=[entry],
            config_root=tmp_path,
        )

    assert installed_bub is None
    assert installed_contrib == ["bub-codex"]
    assert observed["command"] == ["uv", "pip", "install", "--no-sources", str(package_dir.resolve())]


def test_local_contrib_uses_same_install_flow_as_bub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dist_root = tmp_path / "dist"
    config_path = dist_root / "bubseek.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("[project]\nname='demo'\nversion='0.0.1'\n", encoding="utf-8")

    local_contrib = dist_root / "vendor" / "bub-local"
    local_contrib.mkdir(parents=True)
    (local_contrib / "pyproject.toml").write_text("[project]\nname='bub-local'\nversion='0.0.1'\n", encoding="utf-8")

    with imported_bubseek_modules("bubseek.config", "bubseek.sync") as [config_mod, sync_mod]:
        lock_path = dist_root / "bubseek.lock"
        lock_path.write_text(
            "\n".join([
                "[meta]",
                "lock_version = 1",
                'config_file = "bubseek.toml"',
                f'config_sha256 = "{config_mod.sha256_file(config_path)}"',
                "",
                "[[contrib]]",
                'name = "bub-local"',
                'kind = "local"',
                'path = "vendor/bub-local"',
                f'sha256 = "{config_mod.sha256_package_dir(local_contrib)}"',
                "",
            ]),
            encoding="utf-8",
        )

        observed: dict[str, object] = {}

        def _capture_command(command: list[str]) -> None:
            observed["command"] = command

        monkeypatch.setattr(sync_mod, "_run_command", _capture_command)
        installed_bub, installed_contrib = sync_mod._install_distribution_packages(
            bub_entry=None,
            contrib_entries=config_mod.locked_contrib_entries(config_mod.load_lock(lock_path)),
            config_root=dist_root,
        )

    assert installed_bub is None
    assert installed_contrib == ["bub-local"]
    assert observed["command"] == ["uv", "pip", "install", "--no-sources", str(local_contrib.resolve())]
