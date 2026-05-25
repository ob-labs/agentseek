"""Tests for ``agentseek create``: template discovery, listing, and generation."""

from __future__ import annotations

from pathlib import Path

import pytest
from agentseek_cli.app import build_app
from agentseek_cli.commands import create as create_module
from typer.testing import CliRunner


def _runner() -> CliRunner:
    return CliRunner()


def test_unknown_type_exits_2() -> None:
    result = _runner().invoke(build_app(), ["create", "not-a-real-type"])
    assert result.exit_code == 2
    # argparse rejects the unknown choice before our hand-written check runs.
    assert "invalid choice" in result.output or "Unknown framework type" in result.output


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


def test_template_resolution_failure_exits_2() -> None:
    result = _runner().invoke(
        build_app(),
        ["create", "deepagents", "--template", "does-not-exist", "--no-input"],
    )
    assert result.exit_code == 2
    assert "Template 'does-not-exist' not found" in result.output


def test_create_with_explicit_template_invokes_cookiecutter(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_runner(template_path: Path, *, output_dir: Path, no_input: bool) -> None:
        captured["template_path"] = template_path
        captured["output_dir"] = output_dir
        captured["no_input"] = no_input
        # Simulate cookiecutter generating a project so we can assert on it later.
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
    template_path = captured["template_path"]
    assert isinstance(template_path, Path)
    assert template_path.name == "default"
    assert template_path.parent.name == "deepagents"
    assert (template_path / "cookiecutter.json").is_file()
    assert captured["no_input"] is True
    assert Path(str(captured["output_dir"])) == tmp_path
    assert (tmp_path / "fake-project" / "README.md").read_text(encoding="utf-8") == "ok"


def test_create_real_cookiecutter_generates_files(tmp_path: Path) -> None:
    """End-to-end: actually run cookiecutter on a bundled template."""
    pytest.importorskip("cookiecutter")
    from cookiecutter.main import cookiecutter

    templates_root = create_module._templates_root()
    template_path = templates_root / "deepagents" / "default"
    assert (template_path / "cookiecutter.json").is_file()

    output = cookiecutter(str(template_path), output_dir=str(tmp_path), no_input=True)
    generated = Path(output)
    assert generated.is_dir()
    assert (generated / "pyproject.toml").is_file()
    assert (generated / "src").is_dir()
    # The default cookiecutter.json declares "My DeepAgent" → "my_deepagent".
    assert generated.name == "my_deepagent"
    settings_py = generated / "src" / "my_deepagent" / "settings.py"
    assert settings_py.is_file()
    content = settings_py.read_text(encoding="utf-8")
    assert "AGENTSEEK_MODEL" in content


def test_resolve_template_returns_existing_path() -> None:
    path = create_module._resolve_template("bub", "default")
    assert (path / "cookiecutter.json").is_file()


def test_list_templates_unknown_type_returns_empty() -> None:
    assert create_module._list_templates("totally-not-a-type") == []
