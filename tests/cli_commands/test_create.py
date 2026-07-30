"""Tests for ``agentseek create``: template discovery, listing, and generation."""

from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
import tempfile
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PureWindowsPath
from threading import Event, Lock
from typing import TypedDict

import pytest
from filelock import Timeout as FileLockTimeout
from typer.testing import CliRunner

from agentseek.cli.commands import create as create_module
from agentseek.cli.commands.create import TemplateSource
from tests.cli_commands.helpers import build_command_app

pytestmark = pytest.mark.usefixtures("create_symlink")


_CATALOG_COMMIT = "0123456789abcdef0123456789abcdef01234567"
_OTHER_CATALOG_COMMIT = "89abcdef0123456789abcdef0123456789abcdef"
_CATALOG_URL = "https://example.com/teams/agentseek-templates.git"


def test_module_symlink_fixture_does_not_skip_regular_tmp_path_tests(tmp_path: Path) -> None:
    """The symlink fallback must not intercept pytest's own tmp-path setup."""

    assert tmp_path.is_dir()


class _ExplicitCatalogState(TypedDict):
    cached_head: str | None
    fetched_head: str | None
    pristine: bool


def _runner() -> CliRunner:
    return CliRunner()


def _run_git_fixture(*args: str) -> None:
    subprocess.run(  # noqa: S603
        ["git", *args],  # noqa: S607
        check=True,
        capture_output=True,
        text=True,
    )


def _mock_remote_template_repo(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    index: dict[str, str],
    *,
    cached: bool = False,
) -> list[tuple[str, str | None, str, bool]]:
    cookiecutters_dir = tmp_path / "cookiecutters"
    repo_root = cookiecutters_dir / "agentseek" if cached else tmp_path / "downloaded-agentseek"
    templates_root = repo_root / "templates"
    templates_root.mkdir(parents=True)
    (templates_root / "index.json").write_text(json.dumps(index), encoding="utf-8")
    for template in index:
        template_dir = templates_root / template
        template_dir.mkdir(parents=True)
        (template_dir / "cookiecutter.json").write_text(
            json.dumps({"project_slug": "demo"}),
            encoding="utf-8",
        )
        project_file = template_dir / "{{cookiecutter.project_slug}}" / "README.md"
        project_file.parent.mkdir()
        project_file.write_text("# Demo\n", encoding="utf-8")
    clone_calls: list[tuple[str, str | None, str, bool]] = []

    def fake_get_user_config() -> dict[str, str]:
        return {"cookiecutters_dir": str(cookiecutters_dir)}

    def fake_clone(
        repo_url: str,
        *,
        checkout: str | None = None,
        clone_to_dir: Path | str = ".",
        no_input: bool = False,
    ) -> str:
        clone_calls.append((repo_url, checkout, str(clone_to_dir), no_input))
        return str(repo_root)

    monkeypatch.setattr(create_module, "_local_templates_root", lambda: None)
    monkeypatch.setattr("cookiecutter.config.get_user_config", fake_get_user_config)
    monkeypatch.setattr("cookiecutter.vcs.clone", fake_clone)
    return clone_calls


def _mock_local_templates_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    index: dict[str, str],
) -> Path:
    templates_root = tmp_path / "templates"
    templates_root.mkdir()
    (templates_root / "index.json").write_text(json.dumps(index), encoding="utf-8")
    for template in index:
        template_dir = templates_root / template
        template_dir.mkdir(parents=True)
        (template_dir / "cookiecutter.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(create_module, "_local_templates_root", lambda: templates_root)
    return templates_root


def _use_local_default_catalog(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep command-shape tests focused below the locked resolver boundary."""
    templates_root = Path(__file__).resolve().parents[2] / "templates"
    monkeypatch.setattr(
        create_module,
        "_prepare_default_catalog",
        lambda checkout=None: create_module._catalog_from_root(templates_root, source_policy="local-core"),
    )


# -- spec validation / error paths -----------------------------------------


def test_help_exits_0() -> None:
    result = _runner().invoke(build_command_app(), ["create", "--help"])
    assert result.exit_code == 0
    assert "agentseek create" in result.output


def test_unknown_type_exits_2() -> None:
    result = _runner().invoke(build_command_app(), ["create", "not-a-real-type"])
    assert result.exit_code == 2
    assert "Unknown framework type" in result.output
    for project_type in create_module.KNOWN_TYPES:
        assert project_type in result.output


def test_list_templates_for_type_prints_bundled_names() -> None:
    templates = create_module._list_templates("bub")
    assert len(templates) >= 1
    result = _runner().invoke(build_command_app(), ["create", "bub", "--list-templates"])
    assert result.exit_code == 0
    assert "bub" in result.output
    for name in templates:
        assert name in result.output


def test_list_templates_without_type_lists_all_known_types() -> None:
    result = _runner().invoke(build_command_app(), ["create", "--list-templates"])
    assert result.exit_code == 0
    for project_type in create_module.KNOWN_TYPES:
        assert project_type in result.output


def test_list_templates_filter_matches_specs_and_descriptions(monkeypatch, tmp_path: Path) -> None:
    result = _runner().invoke(build_command_app(), ["create", "--list-templates", "--filter", "LANGGRAPH"])

    assert result.exit_code == 0, result.output
    assert "langchain/cli-remote" in result.output
    assert "Remote LangGraph CLI agent" in result.output
    assert "deepagents/default" not in result.output
    assert "bub/default" not in result.output


def test_list_templates_filter_for_type_only_prints_matching_templates(monkeypatch, tmp_path: Path) -> None:
    result = _runner().invoke(build_command_app(), ["create", "langchain", "--list-templates", "--filter", "hybrid"])

    assert result.exit_code == 0, result.output
    assert "langchain/agentic-rag-hybrid" in result.output
    assert "langchain/default" not in result.output
    assert "bub/default" not in result.output


def test_list_templates_filter_no_match_prints_empty_result(monkeypatch, tmp_path: Path) -> None:
    _mock_local_templates_root(
        monkeypatch,
        tmp_path,
        {
            "langchain/graph": "Remote LangGraph starter.",
            "langchain/chat": "Chat-only starter.",
        },
    )

    result = _runner().invoke(
        build_command_app(),
        ["create", "langchain", "--list-templates", "--filter", "not-present"],
    )

    assert result.exit_code == 0, result.output
    assert "No templates matched filter 'not-present' for type 'langchain'." in result.output
    assert "langchain/graph" not in result.output
    assert "langchain/chat" not in result.output


def test_template_flag_no_value_lists_all_templates() -> None:
    """``agentseek create --template`` (no value) should list all templates."""
    result = _runner().invoke(build_command_app(), ["create", "--template"])
    assert result.exit_code == 0
    for project_type in create_module.KNOWN_TYPES:
        assert project_type in result.output
    assert "Usage:" in result.output


def test_template_flag_no_value_with_type_lists_type_templates() -> None:
    """``agentseek create bub --template`` should list bub templates only."""
    templates = create_module._list_templates("bub")
    assert len(templates) >= 1
    result = _runner().invoke(build_command_app(), ["create", "bub", "--template"])
    assert result.exit_code == 0
    assert "bub" in result.output
    for name in templates:
        assert name in result.output
    assert "Usage:" not in result.output


def test_template_flag_unknown_value_lists_type_templates() -> None:
    """A missing --template value should show the supported templates."""
    result = _runner().invoke(build_command_app(), ["create", "bub", "--template", "missing-template"])

    assert result.exit_code == 2
    assert "Template bub/missing-template was not found" in result.output
    assert "Supported templates:" in result.output
    assert "bub/default" in result.output


def test_spec_unknown_template_lists_type_templates() -> None:
    """A missing type/name spec should show the supported templates."""
    result = _runner().invoke(build_command_app(), ["create", "bub/missing-template"])

    assert result.exit_code == 2
    assert "Template bub/missing-template was not found" in result.output
    assert "Supported templates:" in result.output
    assert "bub/default" in result.output


def test_quarantined_contextseek_template_is_not_publicly_selectable(monkeypatch, tmp_path: Path) -> None:
    """Bundled templates omitted from index.json must stay out of create/list/describe."""
    templates = create_module._list_templates("bub")
    assert "contextseek" not in templates

    list_result = _runner().invoke(build_command_app(), ["create", "bub", "--list-templates"])
    assert list_result.exit_code == 0, list_result.output
    assert "bub/default" in list_result.output
    assert "bub/contextseek" not in list_result.output

    all_result = _runner().invoke(build_command_app(), ["create", "--list-templates"])
    assert all_result.exit_code == 0, all_result.output
    assert "bub/default" in all_result.output
    assert "bub/contextseek" not in all_result.output

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> Path:
        pytest.fail("quarantined bundled templates must not reach cookiecutter")

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    describe_result = _runner().invoke(build_command_app(), ["create", "bub/contextseek", "--describe"])
    assert describe_result.exit_code == 2
    assert "Template bub/contextseek was not found" in describe_result.output

    create_result = _runner().invoke(build_command_app(), ["create", "bub/contextseek", "--no-input"])
    assert create_result.exit_code == 2
    assert "Template bub/contextseek was not found" in create_result.output


def test_quarantined_contextseek_template_stays_hidden_from_stale_cache(monkeypatch, tmp_path: Path) -> None:
    """An older cached template index must not re-enable quarantined templates."""
    clone_calls = _mock_remote_template_repo(
        monkeypatch,
        tmp_path,
        {
            "bub/default": "Default Bub template.",
            "bub/contextseek": "Old ContextSeek template.",
            "langchain/default": "Default LangChain template.",
        },
        cached=True,
    )

    list_result = _runner().invoke(build_command_app(), ["create", "bub", "--list-templates"])

    assert list_result.exit_code == 0, list_result.output
    assert clone_calls == []
    assert "bub/default" in list_result.output
    assert "bub/contextseek" not in list_result.output
    assert "Old ContextSeek template." not in list_result.output

    describe_result = _runner().invoke(build_command_app(), ["create", "bub/contextseek", "--describe"])

    assert describe_result.exit_code == 2
    assert "Template bub/contextseek was not found" in describe_result.output


# -- template resolution ---------------------------------------------------


def test_resolve_type_template_local() -> None:
    """Local repo should resolve to an on-disk path with cookiecutter.json."""
    local_root = create_module._local_templates_root()
    assert local_root is not None
    source = create_module._resolve_type_template("bub", "default", templates_root=local_root)
    # When running from the repo, template should be a local path.
    template_path = Path(source.template)
    assert template_path.is_dir()
    assert (template_path / "cookiecutter.json").is_file()
    assert source.directory is None  # local path — no directory needed
    assert source.install_source_path == local_root.parent


def test_cookiecutter_source_context_normalizes_windows_paths() -> None:
    """Structured template values use portable paths and shell-safe quoting."""
    source = TemplateSource(
        template="unused",
        install_source_path=PureWindowsPath(r"D:\source trees\agentseek"),
    )

    context = create_module._cookiecutter_source_context(source)

    assert context["_agentseek_source_path"] == r"D:\source trees\agentseek"
    assert context["_agentseek_source_path_posix"] == "D:/source trees/agentseek"
    assert context["_agentseek_source_path_shell"] == "'D:/source trees/agentseek'"


def test_list_templates_returns_names() -> None:
    templates = create_module._list_templates("bub")
    assert len(templates) >= 1
    assert "default" in templates


def test_list_templates_unknown_type_returns_empty() -> None:
    assert create_module._list_templates("totally-not-a-type") == []


# -- type/name spec parsing ------------------------------------------------


def test_spec_with_slash_splits_into_type_and_name() -> None:
    """``bub/default`` → type=bub, name=default."""
    args = create_module._parse_argv(["bub/default", "--no-input"])
    project_type, template_name = create_module._split_spec(args)
    assert project_type == "bub"
    assert template_name == "default"


def test_spec_plain_type_returns_none_name() -> None:
    args = create_module._parse_argv(["bub", "--no-input"])
    project_type, template_name = create_module._split_spec(args)
    assert project_type == "bub"
    assert template_name is None


def test_spec_none_returns_none_none() -> None:
    args = create_module._parse_argv(["--no-input"])
    project_type, template_name = create_module._split_spec(args)
    assert project_type is None
    assert template_name is None


# -- external spec detection -----------------------------------------------


def test_is_external_spec_url() -> None:
    assert create_module._is_external_spec("https://github.com/x/y.git")
    assert create_module._is_external_spec("git@github.com:x/y.git")
    assert create_module._is_external_spec("/opt/my-template")
    assert create_module._is_external_spec(str(PureWindowsPath("C:/templates/demo")))
    assert create_module._is_external_spec(r"C:\templates\demo")
    assert create_module._is_external_spec(r"\\server\share\template")


def test_is_external_spec_local_type() -> None:
    assert not create_module._is_external_spec("bub")
    assert not create_module._is_external_spec("bub/default")


# -- integration with cookiecutter via monkeypatch -------------------------


def _assert_next_steps(output: str, *, project_path: Path, cd_path: str | None = None) -> None:
    display_path = str(project_path)
    if cd_path is None:
        cd_path = create_module._quote_directory_for_shell(display_path)
    cd_command = "Set-Location -LiteralPath" if os.name == "nt" else "cd"
    assert f"Created {display_path}" in output
    assert ("Next (PowerShell):" if os.name == "nt" else "Next:") in output
    assert f"{cd_command} {cd_path}" in output
    assert "agentseek info" in output
    assert "agentseek task --list" in output
    assert "agentseek doctor" in output


def test_quote_directory_for_shell_uses_the_current_platform_convention() -> None:
    path = str(Path("output directory") / "fake project's directory")
    expected = "'" + path.replace("'", "''") + "'" if os.name == "nt" else shlex.quote(path)

    assert create_module._quote_directory_for_shell(path) == expected


@pytest.mark.skipif(os.name != "nt", reason="requires PowerShell")
def test_directory_change_command_preserves_percent_tokens_in_powershell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AGENTSEEK_PERCENT_PROBE", "must-not-expand")
    target = tmp_path / "review%AGENTSEEK_PERCENT_PROBE%directory's & literal"
    target.mkdir()
    command = create_module._directory_change_command(str(target))
    powershell = shutil.which("powershell.exe")
    assert powershell is not None

    result = subprocess.run(  # noqa: S603
        [
            powershell,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            f"{command}; [Console]::Out.WriteLine((Get-Location).Path)",
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert Path(result.stdout.strip()).resolve() == target.resolve()


def _assert_no_next_steps(output: str) -> None:
    assert "Created " not in output
    assert "Next:" not in output
    assert "agentseek info" not in output
    assert "agentseek task --list" not in output
    assert "agentseek doctor" not in output


def test_create_with_explicit_template_invokes_cookiecutter(monkeypatch, tmp_path: Path) -> None:
    _use_local_default_catalog(monkeypatch)
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> Path:
        captured["source"] = source
        captured["output_dir"] = output_dir
        captured["no_input"] = no_input
        # Simulate cookiecutter generating a project.
        target = output_dir / "fake-project"
        target.mkdir(parents=True, exist_ok=True)
        (target / "README.md").write_text("ok", encoding="utf-8")
        return target

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        ["create", "bub", "--template", "default", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.directory is None
    assert "bub" in source.template and "default" in source.template
    assert captured["no_input"] is True
    assert Path(str(captured["output_dir"])) == tmp_path
    assert (tmp_path / "fake-project" / "README.md").read_text(encoding="utf-8") == "ok"
    _assert_next_steps(result.output, project_path=Path("fake-project"))


def test_create_with_output_dir_invokes_cookiecutter_in_selected_directory(monkeypatch, tmp_path: Path) -> None:
    _use_local_default_catalog(monkeypatch)
    captured: dict[str, object] = {}
    output_dir = Path("generated")

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> Path:
        captured["source"] = source
        captured["output_dir"] = output_dir
        captured["no_input"] = no_input
        target = output_dir / "fake-project"
        target.mkdir(parents=True, exist_ok=True)
        return target

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        ["create", "deepagents", "--template", "default", "--output-dir", str(output_dir), "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert "deepagents" in source.template and "default" in source.template
    assert captured["output_dir"] == output_dir
    assert captured["no_input"] is True
    _assert_next_steps(result.output, project_path=Path("generated") / "fake-project")


def test_create_with_slash_spec_invokes_cookiecutter(monkeypatch, tmp_path: Path) -> None:
    """``agentseek create bub/default --no-input`` should resolve correctly."""
    _use_local_default_catalog(monkeypatch)
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> Path:
        captured["source"] = source
        target = output_dir / "fake-project"
        target.mkdir(parents=True, exist_ok=True)
        return target

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        ["create", "bub/default", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.directory is None
    assert "bub" in source.template and "default" in source.template
    _assert_next_steps(result.output, project_path=Path("fake-project"))


def test_create_with_url_spec_passes_through(monkeypatch, tmp_path: Path) -> None:
    """External URL spec should be passed directly to cookiecutter."""
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> Path:
        captured["source"] = source
        captured["output_dir"] = output_dir
        captured["no_input"] = no_input
        target = output_dir / "external project"
        target.mkdir(parents=True, exist_ok=True)
        return target

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        ["create", "https://github.com/foo/bar.git", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.template == "https://github.com/foo/bar.git"
    assert captured["output_dir"] == tmp_path
    assert captured["no_input"] is True
    _assert_next_steps(result.output, project_path=Path("external project"))


def test_create_with_url_spec_and_output_dir_passes_selected_directory(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}
    output_dir = Path("external-output")

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> Path:
        captured["source"] = source
        captured["output_dir"] = output_dir
        captured["no_input"] = no_input
        target = output_dir / "external project"
        target.mkdir(parents=True, exist_ok=True)
        return target

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        [
            "create",
            "https://github.com/foo/bar.git",
            "--output-dir",
            str(output_dir),
            "--no-input",
        ],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.template == "https://github.com/foo/bar.git"
    assert captured["output_dir"] == output_dir
    assert captured["no_input"] is True
    _assert_next_steps(
        result.output,
        project_path=Path("external-output") / "external project",
    )


# -- --describe mode -------------------------------------------------------


def test_describe_prints_template_info(monkeypatch, tmp_path: Path) -> None:
    """``--describe`` should print template description and cookiecutter variables."""
    _use_local_default_catalog(monkeypatch)
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["called"] = True

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        ["create", "bub/default", "--describe"],
    )

    assert result.exit_code == 0, result.output
    assert "bub/default" in result.output
    assert "Description:" in result.output
    assert "Cookiecutter variables" in result.output
    assert "project_name" in result.output
    assert "project_slug" in result.output
    _assert_no_next_steps(result.output)
    # cookiecutter must not have been called
    assert "called" not in captured


def test_describe_does_not_create_files(monkeypatch, tmp_path: Path) -> None:
    """``--describe`` must not run cookiecutter or create any files."""
    _use_local_default_catalog(monkeypatch)

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        pytest.fail("cookiecutter should not be called in --describe mode")

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        ["create", "bub/default", "--describe"],
    )

    assert result.exit_code == 0, result.output
    _assert_no_next_steps(result.output)
    # No files should have been created in the working directory.
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "spec",
    [
        "https://github.com/foo/bar.git",
        "/abs/template",
    ],
)
def test_describe_external_specs_do_not_call_cookiecutter(
    monkeypatch,
    tmp_path: Path,
    spec: str,
) -> None:
    """``--describe`` is limited to bundled templates before external passthrough."""

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        pytest.fail("cookiecutter should not be called in --describe mode")

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        ["create", spec, "--describe"],
    )

    assert result.exit_code == 2
    assert "--describe supports named AgentSeek catalog templates" in result.output
    _assert_no_next_steps(result.output)
    assert list(tmp_path.iterdir()) == []


def test_describe_unknown_template_exits_2() -> None:
    """``--describe`` on an unknown template should exit 2 and list available templates."""
    result = _runner().invoke(
        build_command_app(),
        ["create", "bub/missing-template", "--describe"],
    )

    assert result.exit_code == 2
    assert "Template bub/missing-template was not found" in result.output
    assert "bub/default" in result.output


# -- explicit AgentSeek catalog override ----------------------------------


def _write_catalog_template(template_dir: Path) -> None:
    template_dir.mkdir(parents=True)
    (template_dir / "cookiecutter.json").write_text(
        json.dumps({"project_slug": "demo", "project_name": "Demo"}),
        encoding="utf-8",
    )
    project_file = template_dir / "{{cookiecutter.project_slug}}" / "README.md"
    project_file.parent.mkdir()
    project_file.write_text(f"# {template_dir.parent.name}/{template_dir.name}\n", encoding="utf-8")


def _write_catalog(
    root: Path,
    index: object,
) -> Path:
    templates_root = root / "templates"
    templates_root.mkdir(parents=True)
    (templates_root / "index.json").write_text(json.dumps(index), encoding="utf-8")
    written_keys: set[str] = set()
    if isinstance(index, dict):
        for key in index:
            if not isinstance(key, str) or key.startswith(("/", ".")):
                continue
            if key.casefold() in written_keys:
                continue
            written_keys.add(key.casefold())
            _write_catalog_template(templates_root / key)
    return root


def _mock_explicit_catalog(  # noqa: C901
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    index: object,
    *,
    commit: str = _CATALOG_COMMIT,
    clone_error: Exception | None = None,
    clone_started: Event | None = None,
    clone_release: Event | None = None,
) -> tuple[list[tuple[str, str | None, Path, bool]], _ExplicitCatalogState, Path]:
    source_root = _write_catalog(tmp_path / "catalog-source", index)
    cookiecutters_dir = _explicit_cookiecutters_dir(tmp_path)
    clone_calls: list[tuple[str, str | None, Path, bool]] = []
    state: _ExplicitCatalogState = {
        "cached_head": commit,
        "fetched_head": commit,
        "pristine": True,
    }
    staging_heads: dict[Path, str | None] = {}

    def fail_if_local_templates_are_consulted() -> Path:
        pytest.fail("an explicit catalog must bypass the local core templates")

    def fake_get_user_config() -> dict[str, str]:
        return {"cookiecutters_dir": str(cookiecutters_dir)}

    def fake_clone(
        repo_url: str,
        *,
        checkout: str | None = None,
        clone_to_dir: Path | str = ".",
        no_input: bool = False,
    ) -> str:
        destination_parent = Path(clone_to_dir)
        clone_calls.append((repo_url, checkout, destination_parent, no_input))
        if clone_started is not None:
            clone_started.set()
        if clone_release is not None:
            assert clone_release.wait(timeout=5), "test did not release the coordinated clone"
        if clone_error is not None:
            raise clone_error
        destination = destination_parent / "catalog"
        shutil.copytree(source_root, destination, symlinks=True)
        staging_heads[destination.resolve()] = state["fetched_head"]
        return str(destination)

    def fake_direct_clone(repo_url: str, checkout: str, destination: Path) -> None:
        clone_calls.append((repo_url, checkout, destination, True))
        if clone_started is not None:
            clone_started.set()
        if clone_release is not None:
            assert clone_release.wait(timeout=5), "test did not release the coordinated clone"
        if clone_error is not None:
            raise clone_error
        shutil.copytree(source_root, destination, symlinks=True)
        staging_heads[destination.resolve()] = state["fetched_head"]
        state["pristine"] = True

    def fake_git_head(repo_root: Path) -> str | None:
        staged = staging_heads.get(repo_root.resolve())
        value = staged if staged is not None else state["cached_head"]
        return value if isinstance(value, str) else None

    def fake_git_templates_are_pristine(repo_root: Path) -> bool:
        return bool(state["pristine"])

    monkeypatch.setattr(create_module, "_local_templates_root", fail_if_local_templates_are_consulted)
    monkeypatch.setattr("cookiecutter.config.get_user_config", fake_get_user_config)
    monkeypatch.setattr("cookiecutter.vcs.clone", fake_clone)
    monkeypatch.setattr(create_module, "_clone_explicit_repository", fake_direct_clone, raising=False)
    monkeypatch.setattr(create_module, "_git_head", fake_git_head, raising=False)
    monkeypatch.setattr(create_module, "_git_templates_are_pristine", fake_git_templates_are_pristine, raising=False)
    return clone_calls, state, source_root


def _explicit_args(*args: str, url: str = _CATALOG_URL, commit: str = _CATALOG_COMMIT) -> list[str]:
    return [
        "create",
        *args,
        "--template-repo",
        url,
        "--checkout",
        commit,
    ]


def _catalog_metadata_files(cookiecutters_dir: Path) -> list[Path]:
    matches: list[Path] = []
    for candidate in cookiecutters_dir.rglob("*.json"):
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if (
            isinstance(data, dict)
            and {"schema_version", "repository_url", "commit", "repository_subdirectory"} <= data.keys()
            and candidate.parent.name == data.get("commit")
        ):
            matches.append(candidate)
    return sorted(matches)


def _cached_catalog_repository(metadata_path: Path) -> Path:
    repository_name = getattr(create_module, "EXPLICIT_CATALOG_REPOSITORY_DIR", "repository")
    repository = metadata_path.parent / repository_name
    return repository if repository.is_dir() else metadata_path.parent


def _explicit_cache_paths(
    tmp_path: Path,
    *,
    normalized_url: str = "https://example.com/teams/agentseek-templates",
    commit: str = _CATALOG_COMMIT,
) -> tuple[Path, Path, Path]:
    namespace = _explicit_cookiecutters_dir(tmp_path) / create_module.EXPLICIT_TEMPLATE_REPO_CACHE_DIR
    digest = hashlib.sha256(normalized_url.encode()).hexdigest()
    digest_dir = namespace / digest
    return namespace, digest_dir, digest_dir / commit


def _explicit_cookiecutters_dir(tmp_path: Path) -> Path:
    """Use a short, isolated cache base for deep explicit-cache tests."""

    identifier = hashlib.sha256(f"{tmp_path.parent.name}/{tmp_path.name}".encode()).hexdigest()[:12]
    return (Path(tempfile.gettempdir()) / f"cc-{identifier}").resolve()


@pytest.fixture(autouse=True)
def _cleanup_explicit_catalog_cache(tmp_path: Path) -> Iterator[None]:
    """Remove the short shared cache base after each explicit-catalog test."""

    yield
    shutil.rmtree(_explicit_cookiecutters_dir(tmp_path), ignore_errors=True)


def test_help_documents_template_repo() -> None:
    result = _runner().invoke(build_command_app(), ["create", "--help"])

    assert result.exit_code == 0
    assert "--template-repo" in result.output


def test_cli_reference_documents_all_three_checkout_modes() -> None:
    repository_root = Path(__file__).parents[2]
    english = (repository_root / "docs" / "reference" / "cli.md").read_text(encoding="utf-8")
    chinese = (repository_root / "docs" / "reference" / "cli.zh.md").read_text(encoding="utf-8")

    assert "Direct Cookiecutter source" in english
    assert "Named/default AgentSeek catalog" in english
    assert "Explicit AgentSeek catalog override" in english
    assert "直接 Cookiecutter 源" in chinese
    assert "命名/默认 AgentSeek 模板目录" in chinese
    assert "显式 AgentSeek 模板目录覆盖" in chinese


def test_explicit_catalog_list_validates_type_before_fetch_or_cache_write(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("not-a-real-type", "--list-templates"),
    )

    assert result.exit_code == 2
    assert "Unknown framework type" in result.output
    assert clone_calls == []
    assert not _explicit_cookiecutters_dir(tmp_path).exists()


@pytest.mark.parametrize(
    "checkout",
    [None, "main", "v1.0.0", "0123456", _CATALOG_COMMIT.upper()],
    ids=["missing", "branch", "tag", "abbreviated", "uppercase"],
)
def test_template_repo_requires_full_lowercase_commit(checkout: str | None) -> None:
    argv = ["create", "bub", "--template-repo", _CATALOG_URL]
    if checkout is not None:
        argv += ["--checkout", checkout]

    result = _runner().invoke(build_command_app(), argv)

    assert result.exit_code == 2
    assert "--checkout must be a 40-character lowercase commit SHA" in result.output


@pytest.mark.parametrize(
    "repo_url",
    [
        "http://example.com/catalog.git",
        "git@example.com:catalog.git",
        "https://example.com/catalog.git?",
        "https://example.com/catalog.git?token=secret",
        "https://example.com/catalog.git#",
        "https://example.com/catalog.git#main",
        "https://user:super-secret@example.com/catalog.git",
        "https://example.com/../catalog.git",
        "https://example.com/%2e%2e/catalog.git",
        "https://example.com/%2e%2e%2fcatalog.git",
        "https://example.com/%252e%252e/catalog.git",
        "https://example.com/./catalog.git",
        "https://example.com/%2E/catalog.git",
    ],
    ids=[
        "http",
        "ssh",
        "empty-query",
        "query",
        "empty-fragment",
        "fragment",
        "credentials",
        "dot-dot-segment",
        "encoded-dot-dot-segment",
        "encoded-dot-dot-slash-segment",
        "double-encoded-dot-dot-segment",
        "dot-segment",
        "encoded-dot-segment",
    ],
)
def test_template_repo_rejects_unsafe_repository_urls_without_leaking_credentials(
    monkeypatch: pytest.MonkeyPatch,
    repo_url: str,
) -> None:
    monkeypatch.setattr(
        create_module,
        "_prepare_explicit_catalog",
        lambda coordinate: pytest.fail("invalid repository URLs must be rejected before fetch or cache preparation"),
    )
    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates", url=repo_url),
    )

    assert result.exit_code == 2
    assert "--template-repo must be an HTTPS repository URL without credentials, query, or fragment" in result.output
    assert "super-secret" not in result.output


@pytest.mark.parametrize(
    "spec",
    [
        "https://github.com/foo/bar.git",
        "/abs/template",
        r"C:\templates\demo",
        r"\\server\share\template",
    ],
    ids=["https", "posix-absolute", "windows-drive", "unc"],
)
def test_template_repo_rejects_external_positional_source_before_dispatch(
    monkeypatch: pytest.MonkeyPatch,
    spec: str,
) -> None:
    monkeypatch.setattr(
        create_module,
        "_run_cookiecutter",
        lambda *args, **kwargs: pytest.fail("conflicting sources must not reach cookiecutter"),
    )

    result = _runner().invoke(build_command_app(), _explicit_args(spec))

    assert result.exit_code == 2
    assert "--template-repo cannot be combined with a positional URL or absolute path" in result.output


def test_explicit_catalog_list_filter_describe_and_create_use_one_catalog(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {
            "bub/remote": "Remote-only Bub template.",
            "deepagents/other": "Other catalog template.",
        },
    )
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> Path:
        captured["source"] = source
        captured["context"] = create_module._cookiecutter_source_context(source)
        generated = output_dir / "generated"
        generated.mkdir()
        return generated

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    list_result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates", "--filter", "REMOTE-ONLY"),
    )
    describe_result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub/remote", "--describe"),
    )
    assert "source" not in captured
    create_result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub/remote", "--no-input"),
    )

    assert list_result.exit_code == 0, list_result.output
    assert "bub/remote" in list_result.output
    assert "deepagents/other" not in list_result.output
    assert describe_result.exit_code == 0, describe_result.output
    assert "Remote-only Bub template." in describe_result.output
    assert create_result.exit_code == 0, create_result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert Path(source.template).is_absolute()
    assert source.install_source_path is None
    assert captured["context"] == {
        "_agentseek_source_path": "",
        "_agentseek_source_path_posix": "",
        "_agentseek_source_path_shell": "",
        "_agentseek_source_url": create_module.REPO_GIT_URL,
    }
    assert len(clone_calls) == 1
    assert clone_calls[0][0] == _CATALOG_URL
    assert clone_calls[0][1] == _CATALOG_COMMIT
    assert clone_calls[0][3] is True


def test_explicit_catalog_registry_is_not_filtered_by_legacy_core_quarantine(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/contextseek": "Reviewed external ContextSeek template."},
    )

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )

    assert result.exit_code == 0, result.output
    assert "bub/contextseek" in result.output


def test_explicit_catalog_cold_cache_publishes_metadata_and_warm_cache_reuses_it(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    argv = _explicit_args("bub", "--list-templates")

    cold_result = _runner().invoke(build_command_app(), argv)
    warm_result = _runner().invoke(build_command_app(), argv)

    assert cold_result.exit_code == 0, cold_result.output
    assert warm_result.exit_code == 0, warm_result.output
    assert len(clone_calls) == 1
    metadata_files = _catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path))
    assert len(metadata_files) == 1
    metadata = json.loads(metadata_files[0].read_text(encoding="utf-8"))
    assert metadata == {
        "schema_version": 1,
        "repository_url": "https://example.com/teams/agentseek-templates",
        "commit": _CATALOG_COMMIT,
        "repository_subdirectory": "templates",
    }
    metadata_path = str(metadata_files[0])
    assert create_module.EXPLICIT_TEMPLATE_REPO_CACHE_DIR in metadata_path
    repository = _cached_catalog_repository(metadata_files[0])
    assert repository.name == create_module.EXPLICIT_CATALOG_REPOSITORY_DIR
    assert metadata_files[0].parent == repository.parent
    assert metadata_files[0].parent != repository


def test_explicit_catalog_committed_metadata_symlink_cannot_write_outside_staging(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, source_root = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    outside_metadata = tmp_path / "outside-metadata.json"
    outside_metadata.write_text("do not touch", encoding="utf-8")
    (source_root / create_module.EXPLICIT_CATALOG_METADATA).symlink_to(outside_metadata)

    list_result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )
    describe_result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub/remote", "--describe"),
    )

    assert list_result.exit_code == 0, list_result.output
    assert describe_result.exit_code == 0, describe_result.output
    assert outside_metadata.read_text(encoding="utf-8") == "do not touch"
    metadata_path = _catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path))[0]
    repository = _cached_catalog_repository(metadata_path)
    assert metadata_path.parent == repository.parent
    assert (repository / create_module.EXPLICIT_CATALOG_METADATA).is_symlink()


def test_explicit_catalog_uses_fixed_git_destination_for_suffix_free_namespace_basename(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    monkeypatch.setattr(
        "cookiecutter.vcs.clone",
        lambda *args, **kwargs: pytest.fail("explicit catalogs must not use Cookiecutter clone"),
    )
    repository_url = "https://git.example/team/agentseek-explicit-catalogs"

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates", url=repository_url),
    )

    assert result.exit_code == 0, result.output
    assert len(clone_calls) == 1
    assert clone_calls[0][0] == repository_url
    clone_destination = clone_calls[0][2]
    assert clone_destination.name == create_module.EXPLICIT_CATALOG_REPOSITORY_DIR
    namespace, _, _ = _explicit_cache_paths(
        tmp_path,
        normalized_url=repository_url,
    )
    assert namespace.is_dir()


@pytest.mark.parametrize(
    "stale_part",
    ["metadata-url", "metadata-commit", "metadata-symlink", "head"],
)
def test_explicit_catalog_rejects_stale_cache_provenance(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    stale_part: str,
) -> None:
    clone_calls, state, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    argv = _explicit_args("bub", "--list-templates")
    first_result = _runner().invoke(build_command_app(), argv)
    assert first_result.exit_code == 0, first_result.output

    if stale_part.startswith("metadata-"):
        metadata_file = _catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path))[0]
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        if stale_part == "metadata-url":
            metadata["repository_url"] = "https://example.com/wrong/catalog"
            metadata_file.write_text(json.dumps(metadata), encoding="utf-8")
        elif stale_part == "metadata-commit":
            metadata["commit"] = _OTHER_CATALOG_COMMIT
            metadata_file.write_text(json.dumps(metadata), encoding="utf-8")
        else:
            external_metadata = tmp_path / "external-metadata.json"
            metadata_file.replace(external_metadata)
            metadata_file.symlink_to(external_metadata)
    else:
        state["cached_head"] = _OTHER_CATALOG_COMMIT

    second_result = _runner().invoke(build_command_app(), argv)

    assert second_result.exit_code == 0, second_result.output
    assert len(clone_calls) == 2


@pytest.mark.parametrize("damage", ["metadata-json", "deleted-template", "corrupt-template"])
def test_explicit_catalog_repairs_corrupt_warm_cache_and_moves_stale_entry_aside(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    damage: str,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    argv = _explicit_args("bub", "--list-templates")
    first_result = _runner().invoke(build_command_app(), argv)
    assert first_result.exit_code == 0, first_result.output
    metadata_path = _catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path))[0]
    cache_entry = metadata_path.parent
    repository = _cached_catalog_repository(metadata_path)

    if damage == "metadata-json":
        (cache_entry / create_module.EXPLICIT_CATALOG_METADATA).write_text("{", encoding="utf-8")
    elif damage == "deleted-template":
        shutil.rmtree(repository / "templates" / "bub" / "remote")
    else:
        (repository / "templates" / "bub" / "remote" / "cookiecutter.json").write_text("{", encoding="utf-8")

    second_result = _runner().invoke(build_command_app(), argv)

    assert second_result.exit_code == 0, second_result.output
    assert len(clone_calls) == 2
    metadata_files = _catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path))
    assert metadata_files == [cache_entry / create_module.EXPLICIT_CATALOG_METADATA]
    repaired_repository = _cached_catalog_repository(metadata_files[0])
    assert (repaired_repository / "templates" / "bub" / "remote" / "cookiecutter.json").is_file()
    assert list(cache_entry.parent.glob(f".{_CATALOG_COMMIT}.stale-*"))


@pytest.mark.parametrize("damage", ["tracked", "untracked", "ignored-hook"])
def test_explicit_catalog_repairs_non_pristine_template_worktree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    damage: str,
) -> None:
    clone_calls, state, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    argv = _explicit_args("bub", "--list-templates")
    first_result = _runner().invoke(build_command_app(), argv)
    assert first_result.exit_code == 0, first_result.output
    repository = _cached_catalog_repository(_catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path))[0])
    injected = repository / "templates" / "bub" / "remote" / "injected.txt"
    if damage == "tracked":
        injected = repository / "templates" / "index.json"
        injected.write_text('{"bub/remote": "tampered"}', encoding="utf-8")
    elif damage == "untracked":
        injected.write_text("untracked", encoding="utf-8")
    else:
        injected = repository / "templates" / "bub" / "remote" / "hooks" / "ignored.py"
        injected.parent.mkdir()
        injected.write_text("ignored", encoding="utf-8")
    state["pristine"] = False

    second_result = _runner().invoke(build_command_app(), argv)

    assert second_result.exit_code == 0, second_result.output
    assert len(clone_calls) == 2
    repaired_repository = _cached_catalog_repository(_catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path))[0])
    if damage == "tracked":
        assert "tampered" not in (repaired_repository / "templates" / "index.json").read_text(encoding="utf-8")
    else:
        assert not (repaired_repository / injected.relative_to(repository)).exists()


@pytest.mark.parametrize("damage", ["tracked", "untracked", "ignored"])
def test_git_templates_pristine_rejects_every_worktree_change(tmp_path: Path, damage: str) -> None:
    repository = tmp_path / "repository"
    template_file = repository / "templates" / "bub" / "default" / "cookiecutter.json"
    template_file.parent.mkdir(parents=True)
    template_file.write_text("{}", encoding="utf-8")
    (repository / ".gitignore").write_text("templates/**/ignored.txt\n", encoding="utf-8")
    _run_git_fixture("init", str(repository))
    _run_git_fixture("-C", str(repository), "config", "user.email", "tests@example.com")
    _run_git_fixture("-C", str(repository), "config", "user.name", "AgentSeek tests")
    _run_git_fixture("-C", str(repository), "add", ".")
    _run_git_fixture("-C", str(repository), "commit", "-m", "fixture")
    assert create_module._git_templates_are_pristine(repository)

    if damage == "tracked":
        template_file.write_text('{"changed": true}', encoding="utf-8")
    elif damage == "untracked":
        (template_file.parent / "untracked.txt").write_text("new", encoding="utf-8")
    else:
        (template_file.parent / "ignored.txt").write_text("ignored", encoding="utf-8")

    assert not create_module._git_templates_are_pristine(repository)


@pytest.mark.parametrize("metadata_damage", ["boolean-schema", "extra-key"])
def test_explicit_catalog_metadata_requires_exact_keys_and_field_types(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    metadata_damage: str,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    argv = _explicit_args("bub", "--list-templates")
    first_result = _runner().invoke(build_command_app(), argv)
    assert first_result.exit_code == 0, first_result.output
    metadata_path = _catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path))[0]
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata_damage == "boolean-schema":
        metadata["schema_version"] = True
    else:
        metadata["unexpected"] = "not part of schema 1"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    second_result = _runner().invoke(build_command_app(), argv)

    assert second_result.exit_code == 0, second_result.output
    assert len(clone_calls) == 2


@pytest.mark.parametrize("symlink_part", ["namespace", "digest", "commit"])
def test_explicit_catalog_rejects_symlinked_cache_ancestors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    symlink_part: str,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    namespace, digest_dir, cache_entry = _explicit_cache_paths(tmp_path)
    outside = tmp_path / f"outside-{symlink_part}"
    outside.mkdir()
    if symlink_part == "namespace":
        namespace.parent.mkdir(parents=True)
        namespace.symlink_to(outside, target_is_directory=True)
    elif symlink_part == "digest":
        namespace.mkdir(parents=True)
        digest_dir.symlink_to(outside, target_is_directory=True)
    else:
        digest_dir.mkdir(parents=True)
        cache_entry.symlink_to(outside, target_is_directory=True)

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )

    assert result.exit_code == 1
    assert "explicit template catalog" in result.output.lower()
    assert clone_calls == []


@pytest.mark.parametrize("link_part", ["namespace", "digest", "commit"])
def test_explicit_catalog_rejects_windows_reparse_like_cache_ancestors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    link_part: str,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    namespace, digest_dir, cache_entry = _explicit_cache_paths(tmp_path)
    selected = {"namespace": namespace, "digest": digest_dir, "commit": cache_entry}[link_part]
    original = getattr(create_module, "_path_is_link_like", lambda path: path.is_symlink())

    def fake_link_like(path: Path) -> bool:
        return Path(path) == selected or original(Path(path))

    monkeypatch.setattr(create_module, "_path_is_link_like", fake_link_like, raising=False)

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )

    assert result.exit_code == 1
    assert "explicit template catalog" in result.output.lower()
    assert clone_calls == []


def test_explicit_catalog_publishers_share_coordinate_lock_and_one_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_started = Event()
    clone_release = Event()
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
        clone_started=clone_started,
        clone_release=clone_release,
    )
    coordinate = create_module._explicit_catalog_coordinate(
        create_module._parse_argv(["bub", "--template-repo", _CATALOG_URL, "--checkout", _CATALOG_COMMIT])
    )
    assert coordinate is not None
    second_lock_attempt = Event()
    acquisition_guard = Lock()
    acquisition_attempts = 0
    original_acquire = create_module.FileLock.acquire

    def acquire(lock: create_module.FileLock) -> object:
        nonlocal acquisition_attempts
        with acquisition_guard:
            acquisition_attempts += 1
            if acquisition_attempts == 2:
                second_lock_attempt.set()
        return original_acquire(lock)

    monkeypatch.setattr(create_module.FileLock, "acquire", acquire)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(create_module._prepare_explicit_catalog, coordinate)
        assert clone_started.wait(timeout=5)
        second = executor.submit(create_module._prepare_explicit_catalog, coordinate)
        assert second_lock_attempt.wait(timeout=5)
        clone_release.set()
        prepared = [first.result(timeout=5), second.result(timeout=5)]

    roots: list[Path] = []
    for item in prepared:
        assert item.templates_root is not None
        roots.append(item.templates_root)
    assert acquisition_attempts == 2
    assert len(clone_calls) == 1
    assert roots[0] == roots[1]
    assert all((Path(root) / "bub" / "remote" / "cookiecutter.json").is_file() for root in roots)


def test_explicit_catalog_lock_timeout_rechecks_cache_before_failing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_calls, _, source_root = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    prepared = create_module._prepared_catalog(
        source_root / "templates",
        {"bub/remote": "Remote template."},
        source_policy="explicit",
    )
    validations = 0
    constructed: list[tuple[Path, float]] = []

    def validate_cache(
        cache_entry: Path,
        coordinate: create_module._ExplicitCatalogCoordinate,
    ) -> create_module._PreparedCatalog | None:
        nonlocal validations
        validations += 1
        return prepared if validations == 2 else None

    class TimedOutLock:
        def __init__(self, path: Path, *, timeout: float) -> None:
            constructed.append((Path(path), timeout))

        def __enter__(self) -> object:
            raise FileLockTimeout(str(constructed[-1][0]))

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(create_module, "_validated_explicit_catalog_cache", validate_cache)
    monkeypatch.setattr(create_module, "FileLock", TimedOutLock)

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )

    assert result.exit_code == 0, result.output
    assert validations == 2
    assert constructed[0][1] == create_module.EXPLICIT_CATALOG_LOCK_TIMEOUT_SECONDS
    assert clone_calls == []


def test_explicit_catalog_lock_timeout_is_generic_when_cache_stays_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )

    class TimedOutLock:
        def __init__(self, path: Path, *, timeout: float) -> None:
            assert timeout == create_module.EXPLICIT_CATALOG_LOCK_TIMEOUT_SECONDS
            self.path = path

        def __enter__(self) -> object:
            raise FileLockTimeout(str(self.path))

        def __exit__(self, *args: object) -> None:
            return None

    monkeypatch.setattr(create_module, "FileLock", TimedOutLock)

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )

    assert result.exit_code == 1
    assert result.output.strip() == "Could not prepare the explicit template catalog."
    assert clone_calls == []


def test_explicit_catalog_selection_uses_validated_registry_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    original_prepare = create_module._prepare_explicit_catalog

    def prepare_then_mutate_registry(
        coordinate: create_module._ExplicitCatalogCoordinate,
    ) -> create_module._PreparedCatalog:
        prepared = original_prepare(coordinate)
        templates_root = prepared.templates_root
        assert templates_root is not None
        index_path = templates_root / "index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["bub/unregistered"] = "Added after strict preparation."
        index_path.write_text(json.dumps(index), encoding="utf-8")
        template_dir = templates_root / "bub" / "unregistered"
        _write_catalog_template(template_dir)
        return prepared

    monkeypatch.setattr(create_module, "_prepare_explicit_catalog", prepare_then_mutate_registry)
    monkeypatch.setattr(
        create_module,
        "_run_cookiecutter",
        lambda *args, **kwargs: pytest.fail("an unregistered post-prepare template must not generate"),
    )

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub/unregistered", "--describe"),
    )

    assert result.exit_code == 2
    assert "Template bub/unregistered was not found" in result.output
    assert "bub/remote" in result.output


def test_explicit_catalog_cache_normalizes_url_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )

    first_result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates", url="HTTPS://EXAMPLE.COM:443/teams/agentseek-templates.git/"),
    )
    second_result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates", url="https://example.com/teams/agentseek-templates"),
    )

    assert first_result.exit_code == 0, first_result.output
    assert second_result.exit_code == 0, second_result.output
    assert len(clone_calls) == 1
    assert clone_calls[0][0] == "HTTPS://EXAMPLE.COM:443/teams/agentseek-templates.git/"


def test_explicit_catalog_accepts_https_repository_at_host_root(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_calls, _, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates", url="https://git.example/"),
    )

    assert result.exit_code == 0, result.output
    assert clone_calls[0][0] == "https://git.example/"
    metadata = json.loads(_catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path))[0].read_text(encoding="utf-8"))
    assert metadata["repository_url"] == "https://git.example"


def test_explicit_catalog_git_adapter_clones_fixed_destination_and_verifies_head(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    destination = tmp_path / "candidate" / "repository"
    destination.parent.mkdir()
    commands: list[list[str]] = []

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        assert kwargs["timeout"] == create_module.EXPLICIT_CATALOG_GIT_TIMEOUT_SECONDS
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is True
        assert kwargs["check"] is True
        if command[1] == "clone":
            destination.mkdir(parents=True)
        stdout = f"{_CATALOG_COMMIT}\n" if command[-2:] == ["rev-parse", "HEAD"] else ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(create_module.subprocess, "run", fake_run)

    create_module._clone_explicit_repository(_CATALOG_URL, _CATALOG_COMMIT, destination)

    assert commands[0] == ["git", "clone", "--no-checkout", "--", _CATALOG_URL, str(destination)]
    assert commands[1] == ["git", "-C", str(destination), "checkout", "--detach", _CATALOG_COMMIT]
    assert commands[2] == ["git", "-C", str(destination), "rev-parse", "HEAD"]


def test_explicit_catalog_git_adapter_timeout_is_secret_safe_and_does_not_publish(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    repository_url = "https://user:" + "secret@example.com/catalog"
    destination = tmp_path / "candidate" / "repository"
    destination.parent.mkdir()

    def timed_out(command: list[str], **kwargs: object) -> object:
        timeout = kwargs["timeout"]
        assert isinstance(timeout, (int, float))
        raise subprocess.TimeoutExpired(command, timeout)

    monkeypatch.setattr(create_module.subprocess, "run", timed_out)

    with pytest.raises(create_module._InvalidExplicitCatalog) as caught:
        create_module._clone_explicit_repository(repository_url, _CATALOG_COMMIT, destination)

    assert "secret" not in str(caught.value)
    assert "example.com" not in str(caught.value)
    assert not destination.exists()


def test_explicit_catalog_cache_isolates_same_basename_urls_and_commits(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_calls, state, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )

    results = [
        _runner().invoke(
            build_command_app(),
            _explicit_args("bub", "--list-templates", url="https://one.example/team/catalog.git"),
        ),
        _runner().invoke(
            build_command_app(),
            _explicit_args("bub", "--list-templates", url="https://two.example/other/catalog.git"),
        ),
    ]
    state["fetched_head"] = _OTHER_CATALOG_COMMIT
    results.append(
        _runner().invoke(
            build_command_app(),
            _explicit_args("bub", "--list-templates", commit=_OTHER_CATALOG_COMMIT),
        )
    )

    assert all(result.exit_code == 0 for result in results), [result.output for result in results]
    assert len(clone_calls) == 3
    assert len(_catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path))) == 3


def test_explicit_catalog_rejects_wrong_fetched_head_without_publishing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    clone_calls, state, _ = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    state["fetched_head"] = _OTHER_CATALOG_COMMIT

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )

    assert result.exit_code == 1
    assert "HEAD does not match --checkout" in result.output
    assert len(clone_calls) == 1
    assert _catalog_metadata_files(_explicit_cookiecutters_dir(tmp_path)) == []


def test_explicit_catalog_fetch_failure_does_not_fall_back(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
        clone_error=RuntimeError("network unavailable"),
    )
    monkeypatch.setattr(
        create_module,
        "_run_cookiecutter",
        lambda *args, **kwargs: pytest.fail("a failed explicit fetch must not generate"),
    )

    result = _runner().invoke(build_command_app(), _explicit_args("bub/remote", "--no-input"))

    assert result.exit_code == 1
    assert "Could not prepare the explicit template catalog" in result.output
    assert "bub/default" not in result.output


@pytest.mark.parametrize(
    ("index", "expected"),
    [
        ({}, "non-empty object"),
        ([], "non-empty object"),
        ({"../escape": "Unsafe key."}, "safe type/name"),
        ({"bub/remote": 42}, "descriptions must be strings"),
        ({"bub/CON": "Windows reserved name."}, "portable type/name"),
        ({"bub/template.": "Trailing dot."}, "portable type/name"),
        (
            {"bub/Remote": "First.", "BUB/remote": "Second."},
            "case-insensitive duplicate",
        ),
    ],
    ids=[
        "empty",
        "not-object",
        "unsafe-key",
        "non-string-description",
        "windows-reserved",
        "trailing-dot",
        "casefold-collision",
    ],
)
def test_explicit_catalog_rejects_invalid_registry_without_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    index: object,
    expected: str,
) -> None:
    _mock_explicit_catalog(monkeypatch, tmp_path, index)

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )

    assert result.exit_code == 1
    assert "Explicit template catalog is invalid" in result.output
    assert expected in result.output


def test_explicit_catalog_escapes_terminal_controls_in_descriptions_and_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, source_root = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote\x1b[31m\nInjected\x07"},
    )
    context_path = source_root / "templates" / "bub" / "remote" / "cookiecutter.json"
    context = json.loads(context_path.read_text(encoding="utf-8"))
    context["project_name"] = "Demo\rOverwrite\x00"
    context["\x1b]0;owned\x07"] = "safe"
    context_path.write_text(json.dumps(context), encoding="utf-8")

    list_result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )
    describe_result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub/remote", "--describe"),
    )

    combined = list_result.output + describe_result.output
    assert list_result.exit_code == 0, list_result.output
    assert describe_result.exit_code == 0, describe_result.output
    assert all(control not in combined for control in ("\x00", "\x07", "\r", "\x1b"))
    assert "Remote\\x1b[31m\\x0aInjected\\x07" in combined
    assert "Demo\\x0dOverwrite\\x00" in combined
    assert "\\x1b]0;owned\\x07: safe" in combined


@pytest.mark.parametrize(
    "damage",
    ["missing-config", "invalid-config", "missing-project-slug", "empty-body"],
)
def test_explicit_catalog_rejects_incomplete_registered_template(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    damage: str,
) -> None:
    _, _, source_root = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    template_dir = source_root / "templates" / "bub" / "remote"
    if damage == "missing-config":
        (template_dir / "cookiecutter.json").unlink()
    elif damage == "invalid-config":
        (template_dir / "cookiecutter.json").write_text("{", encoding="utf-8")
    elif damage == "missing-project-slug":
        (template_dir / "cookiecutter.json").write_text("{}", encoding="utf-8")
    else:
        shutil.rmtree(template_dir / "{{cookiecutter.project_slug}}")
        (template_dir / "{{cookiecutter.project_slug}}").mkdir()

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )

    assert result.exit_code == 1
    assert "Explicit template catalog is invalid" in result.output
    assert "bub/remote" in result.output


def test_explicit_catalog_rejects_template_symlink_escape(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _, _, source_root = _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("secret", encoding="utf-8")
    (source_root / "templates" / "bub" / "remote" / "{{cookiecutter.project_slug}}" / "escape.txt").symlink_to(outside)

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )

    assert result.exit_code == 1
    assert "Explicit template catalog is invalid" in result.output
    assert "symlink" in result.output


@pytest.mark.parametrize("link_part", ["repository", "templates", "template", "nested"])
def test_explicit_catalog_rejects_windows_reparse_like_repository_content(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    link_part: str,
) -> None:
    _mock_explicit_catalog(
        monkeypatch,
        tmp_path,
        {"bub/remote": "Remote template."},
    )
    original = getattr(create_module, "_path_is_link_like", lambda path: path.is_symlink())

    def fake_link_like(path: Path) -> bool:
        candidate = Path(path)
        selected = {
            "repository": candidate.name == "repository" and candidate.parent.name == "candidate",
            "templates": candidate.name == "templates",
            "template": candidate.name == "remote",
            "nested": candidate.name == "README.md",
        }[link_part]
        return selected or original(candidate)

    monkeypatch.setattr(create_module, "_path_is_link_like", fake_link_like, raising=False)

    result = _runner().invoke(
        build_command_app(),
        _explicit_args("bub", "--list-templates"),
    )

    assert result.exit_code == 1
    assert "Explicit template catalog is invalid" in result.output
    assert "link" in result.output.lower()


@pytest.mark.parametrize(
    "spec",
    [
        "https://github.com/foo/bar.git",
        "/opt/templates/demo",
        r"C:\templates\demo",
        r"\\server\share\template",
    ],
    ids=["https", "posix-absolute", "windows-drive", "unc"],
)
def test_positional_cookiecutter_source_keeps_checkout_and_directory_passthrough(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    spec: str,
) -> None:
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_command_app(),
        [
            "create",
            spec,
            "--checkout",
            "release/next",
            "--template",
            "nested/template",
        ],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.template == spec
    assert source.checkout == "release/next"
    assert source.directory == "nested/template"
