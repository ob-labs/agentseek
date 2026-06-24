"""Render-check regression test for every cookiecutter template under ``templates/``.

For each template, render it with ``no_input=True`` (using ``cookiecutter.json``
defaults) into a temporary directory and assert the generated tree carries the
invariants every template must satisfy.

This test does *not* install dependencies, run ``uv sync``, or boot the
generated project — that lives in a later smoke script. The point here is to
catch Jinja errors, missing files, and unsubstituted variables before they hit
``main``.
"""

from __future__ import annotations

import json
import shutil
import tomllib
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter
from typer.testing import CliRunner

from agentseek.cli.commands import create as create_module
from tests.cli_commands.helpers import build_command_app


def _patch_template_for_test(template_dir: Path, tmp_path: Path) -> Path:
    """Copy a template dir for isolated cookiecutter rendering."""
    patched = tmp_path / "patched_template" / template_dir.name
    shutil.copytree(template_dir, patched)
    return patched


def _discover_templates() -> list[tuple[str, str, Path]]:
    """Walk ``templates/`` and yield ``(type, name, template_dir)`` for each
    directory that contains a ``cookiecutter.json``.

    Returns an empty list when the templates root cannot be found (e.g. when
    the package is installed without a checkout). The test that consumes this
    asserts non-empty to fail loudly in that case.
    """
    root = create_module._local_templates_root()
    if root is None:
        return []
    discovered: list[tuple[str, str, Path]] = []
    for type_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        for template_dir in sorted(p for p in type_dir.iterdir() if p.is_dir()):
            if (template_dir / "cookiecutter.json").is_file():
                discovered.append((type_dir.name, template_dir.name, template_dir))
    return discovered


TEMPLATES = _discover_templates()


def test_at_least_one_template_discovered() -> None:
    """Sanity check: the harness must see the bundled templates."""
    assert TEMPLATES, (
        "No templates discovered under templates/. Either the templates root "
        "moved or _local_templates_root() can no longer find it."
    )


@pytest.mark.parametrize(
    ("type_name", "template_name", "template_dir"),
    TEMPLATES,
    ids=[f"{t}/{n}" for t, n, _ in TEMPLATES],
)
def test_template_renders_without_unrendered_jinja(
    type_name: str,
    template_name: str,
    template_dir: Path,
    tmp_path: Path,
) -> None:
    """Each template must render with its defaults and leave no Jinja markers."""
    patched = _patch_template_for_test(template_dir, tmp_path)
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    cookiecutter(
        template=str(patched),
        output_dir=str(out_dir),
        no_input=True,
    )

    generated = next(p for p in out_dir.iterdir() if p.is_dir())

    pyproject = generated / "pyproject.toml"
    assert pyproject.is_file(), f"missing pyproject.toml in {generated}"
    pyproject_text = pyproject.read_text(encoding="utf-8")
    assert "{{" not in pyproject_text, (
        f"unrendered Jinja in {pyproject}: contains '{{{{' — a cookiecutter "
        "variable was referenced but not substituted."
    )
    pyproject_data = tomllib.loads(pyproject_text)
    assert pyproject_data["project"]["name"]
    dependencies = pyproject_data["project"].get("dependencies", [])
    assert isinstance(dependencies, list)
    if (type_name, template_name) == ("bub", "default"):
        assert "bub==0.3.9" in dependencies
        assert "agentseek-ag-ui" in dependencies
        assert "duty>=1.9" not in pyproject_data.get("dependency-groups", {}).get("dev", [])

    lifecycle = generated / ".agentseek" / "lifecycle.toml"
    assert lifecycle.is_file(), f"missing .agentseek/lifecycle.toml in {generated}"
    lifecycle_text = lifecycle.read_text(encoding="utf-8")
    assert "{{" not in lifecycle_text, (
        f"unrendered Jinja in {lifecycle}: contains '{{{{' — a cookiecutter "
        "variable was referenced but not substituted."
    )
    lifecycle_data = tomllib.loads(lifecycle_text)
    assert lifecycle_data["template"] == f"{type_name}/{template_name}"
    assert lifecycle_data["processes"]
    assert not (generated / "duties.py").exists()

    frontend_pkg = generated / "frontend" / "package.json"
    if frontend_pkg.is_file():
        try:
            json.loads(frontend_pkg.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            pytest.fail(f"frontend/package.json is not valid JSON: {exc}")


@pytest.mark.parametrize(
    ("type_name", "template_name", "template_dir"),
    TEMPLATES,
    ids=[f"{t}/{n}" for t, n, _ in TEMPLATES],
)
def test_template_lifecycle_commands_smoke(
    type_name: str,
    template_name: str,
    template_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rendered templates expose the AgentSeek lifecycle commands."""
    patched = _patch_template_for_test(template_dir, tmp_path)
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    cookiecutter(
        template=str(patched),
        output_dir=str(out_dir),
        no_input=True,
    )

    generated = next(p for p in out_dir.iterdir() if p.is_dir())
    assert (generated / ".agentseek" / "lifecycle.toml").is_file()
    monkeypatch.chdir(generated)

    app = build_command_app()
    runner = CliRunner()

    info = runner.invoke(app, ["info"])
    assert info.exit_code == 0, info.stdout + info.stderr
    assert f"Template: {type_name}/{template_name}" in info.stdout

    dev = runner.invoke(app, ["dev", "--dry-run", "--skip-check"])
    assert dev.exit_code == 0, dev.stdout + dev.stderr
    assert "Startup plan" in dev.stdout
