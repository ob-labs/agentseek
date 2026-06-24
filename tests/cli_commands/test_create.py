"""Tests for ``agentseek create``: template discovery, listing, and generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentseek.cli.commands import create as create_module
from agentseek.cli.commands.create import TemplateSource
from tests.cli_commands.helpers import build_command_app


def _runner() -> CliRunner:
    return CliRunner()


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
        (template_dir / "cookiecutter.json").write_text("{}", encoding="utf-8")
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


def test_template_flag_no_value_lists_remote_templates_without_checkout(monkeypatch, tmp_path: Path) -> None:
    """Installed CLI should download templates before listing them."""
    clone_calls = _mock_remote_template_repo(
        monkeypatch,
        tmp_path,
        {
            "bub/default": "Default Bub template.",
            "deepagents/default": "Default DeepAgents template.",
            "langchain/default": "Default LangChain template.",
        },
    )

    result = _runner().invoke(build_command_app(), ["create", "--template"])

    assert result.exit_code == 0, result.output
    assert clone_calls == [(create_module.REPO_URL, None, str(tmp_path / "cookiecutters"), True)]
    assert "bub/default" in result.output
    assert "Default Bub template." in result.output
    assert "deepagents/default" in result.output
    assert "Default DeepAgents template." in result.output
    assert "langchain/default" in result.output
    assert "Default LangChain template." in result.output
    assert "Usage:" in result.output


def test_template_flag_no_value_for_type_uses_remote_checkout(monkeypatch, tmp_path: Path) -> None:
    """``--checkout`` should be forwarded to cookiecutter's clone path."""
    clone_calls = _mock_remote_template_repo(
        monkeypatch,
        tmp_path,
        {"langchain/remote-only": "Remote-only LangChain template."},
    )

    result = _runner().invoke(build_command_app(), ["create", "langchain", "--template", "--checkout", "release/next"])

    assert result.exit_code == 0, result.output
    assert clone_calls == [(create_module.REPO_URL, "release/next", str(tmp_path / "cookiecutters"), True)]
    assert "langchain/remote-only" in result.output
    assert "Usage:" not in result.output


def test_template_flag_no_value_reuses_cached_remote_repo(monkeypatch, tmp_path: Path) -> None:
    """Installed CLI should use the cookiecutter cache before cloning."""
    clone_calls = _mock_remote_template_repo(
        monkeypatch,
        tmp_path,
        {"bub/cached": "Cached Bub template."},
        cached=True,
    )

    result = _runner().invoke(build_command_app(), ["create", "bub", "--template"])

    assert result.exit_code == 0, result.output
    assert clone_calls == []
    assert "bub/cached" in result.output
    assert "Cached Bub template." in result.output


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


def test_is_external_spec_local_type() -> None:
    assert not create_module._is_external_spec("bub")
    assert not create_module._is_external_spec("bub/default")


# -- integration with cookiecutter via monkeypatch -------------------------


def test_create_with_explicit_template_invokes_cookiecutter(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source
        captured["output_dir"] = output_dir
        captured["no_input"] = no_input
        # Simulate cookiecutter generating a project.
        target = output_dir / "fake-project"
        target.mkdir(parents=True, exist_ok=True)
        (target / "README.md").write_text("ok", encoding="utf-8")

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


def test_create_with_slash_spec_invokes_cookiecutter(monkeypatch, tmp_path: Path) -> None:
    """``agentseek create bub/default --no-input`` should resolve correctly."""
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source

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


def test_create_with_url_spec_passes_through(monkeypatch, tmp_path: Path) -> None:
    """External URL spec should be passed directly to cookiecutter."""
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source

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
