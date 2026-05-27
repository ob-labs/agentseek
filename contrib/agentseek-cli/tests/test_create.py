"""Tests for ``agentseek create``: template discovery, listing, and generation."""

from __future__ import annotations

from pathlib import Path

import pytest
from agentseek_cli.app import build_app
from agentseek_cli.commands import create as create_module
from agentseek_cli.commands.create import TemplateSource
from typer.testing import CliRunner


def _runner() -> CliRunner:
    return CliRunner()


# -- spec validation / error paths -----------------------------------------


def test_unknown_type_exits_2() -> None:
    result = _runner().invoke(build_app(), ["create", "not-a-real-type"])
    assert result.exit_code == 2
    assert "Unknown framework type" in result.output


def test_list_templates_for_type_prints_bundled_names() -> None:
    result = _runner().invoke(build_app(), ["create", "langchain", "--list-templates"])
    assert result.exit_code == 0
    assert "Available langchain templates" in result.output
    assert "default" in result.output
    assert "cli-remote" in result.output


def test_list_templates_without_type_lists_all_known_types() -> None:
    result = _runner().invoke(build_app(), ["create", "--list-templates"])
    assert result.exit_code == 0
    for project_type in create_module.KNOWN_TYPES:
        assert f"Available {project_type} templates" in result.output


# -- template resolution ---------------------------------------------------


def test_resolve_type_template_local() -> None:
    """Local repo should resolve to an on-disk path with cookiecutter.json."""
    source = create_module._resolve_type_template("bub", "default")
    # When running from the repo, template should be a local path.
    template_path = Path(source.template)
    assert template_path.is_dir()
    assert (template_path / "cookiecutter.json").is_file()
    assert source.directory is None  # local path — no directory needed


def test_resolve_type_template_remote_fallback(monkeypatch) -> None:
    """When there's no local repo, should fall back to remote URL."""
    monkeypatch.setattr(create_module, "_local_templates_root", lambda: None)
    source = create_module._resolve_type_template("deepagents", "default")
    assert source.template == create_module.REPO_URL
    assert source.directory == "templates/deepagents/default"


def test_list_templates_returns_names() -> None:
    templates = create_module._list_templates("langchain")
    assert "default" in templates
    assert "cli-remote" in templates


def test_list_templates_unknown_type_returns_empty() -> None:
    assert create_module._list_templates("totally-not-a-type") == []


# -- type/name spec parsing ------------------------------------------------


def test_spec_with_slash_splits_into_type_and_name() -> None:
    """``langchain/cli-remote`` → type=langchain, name=cli-remote."""
    args = create_module._parse_argv(["langchain/cli-remote", "--no-input"])
    project_type, template_name = create_module._split_spec(args)
    assert project_type == "langchain"
    assert template_name == "cli-remote"


def test_spec_plain_type_returns_none_name() -> None:
    args = create_module._parse_argv(["deepagents", "--no-input"])
    project_type, template_name = create_module._split_spec(args)
    assert project_type == "deepagents"
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
    assert not create_module._is_external_spec("deepagents")
    assert not create_module._is_external_spec("langchain/cli-remote")


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
        build_app(),
        ["create", "deepagents", "--template", "default", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    # May resolve locally (path with deepagents/default) or remotely (URL + directory).
    if source.directory is not None:
        # Remote fallback: directory carries the subpath.
        assert "deepagents/default" in source.directory
    else:
        # Local: template path ends with deepagents/default.
        assert "deepagents" in source.template and "default" in source.template
    assert captured["no_input"] is True
    assert Path(str(captured["output_dir"])) == tmp_path
    assert (tmp_path / "fake-project" / "README.md").read_text(encoding="utf-8") == "ok"


def test_create_with_slash_spec_invokes_cookiecutter(monkeypatch, tmp_path: Path) -> None:
    """``agentseek create langchain/cli-remote --no-input`` should resolve correctly."""
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_app(),
        ["create", "langchain/cli-remote", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    # May resolve locally or remotely.
    if source.directory is not None:
        assert "langchain/cli-remote" in source.directory
    else:
        assert "langchain" in source.template and "cli-remote" in source.template


def test_create_with_url_spec_passes_through(monkeypatch, tmp_path: Path) -> None:
    """External URL spec should be passed directly to cookiecutter."""
    captured: dict[str, object] = {}

    def fake_runner(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source

    monkeypatch.setattr(create_module, "_run_cookiecutter", fake_runner)
    monkeypatch.chdir(tmp_path)

    result = _runner().invoke(
        build_app(),
        ["create", "https://github.com/foo/bar.git", "--no-input"],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.template == "https://github.com/foo/bar.git"


# -- real cookiecutter end-to-end ------------------------------------------


def test_create_real_cookiecutter_generates_files(tmp_path: Path) -> None:
    """End-to-end: actually run cookiecutter on a local template."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    local_root = create_module._local_templates_root()
    assert local_root is not None, "Tests must run from a git checkout"
    template_path = local_root / "deepagents" / "default"
    assert (template_path / "cookiecutter.json").is_file()

    output = cookiecutter(str(template_path), output_dir=str(tmp_path), no_input=True)
    generated = Path(output)
    assert generated.is_dir()
    assert (generated / "pyproject.toml").is_file()
    assert (generated / "src").is_dir()
    assert generated.name == "my_deepagent"
    settings_py = generated / "src" / "my_deepagent" / "settings.py"
    assert settings_py.is_file()
    content = settings_py.read_text(encoding="utf-8")
    assert "AGENTSEEK_MODEL" in content
