"""Registry consistency checks for bundled cookiecutter templates."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_ROOT = REPO_ROOT / "templates"
INDEX_PATH = TEMPLATES_ROOT / "index.json"


def _registered_templates() -> set[str]:
    registry = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return set(registry)


def _template_dirs() -> set[str]:
    return {
        f"{type_dir.name}/{template_dir.name}"
        for type_dir in TEMPLATES_ROOT.iterdir()
        if type_dir.is_dir()
        for template_dir in type_dir.iterdir()
        if template_dir.is_dir() and (template_dir / "cookiecutter.json").is_file()
    }


def test_all_cookiecutter_templates_are_registered() -> None:
    """Every templates/<type>/<name>/cookiecutter.json entry is in index.json."""
    missing = sorted(_template_dirs() - _registered_templates())

    assert not missing, f"template(s) missing from templates/index.json: {missing}"


def test_registered_templates_point_to_cookiecutter_directories() -> None:
    """Every registry key points to a template directory with cookiecutter.json."""
    stale = sorted(_registered_templates() - _template_dirs())

    assert not stale, f"stale templates/index.json key(s): {stale}"


def test_registered_templates_have_readme() -> None:
    """Every registered template has a top-level README for template users."""
    missing_readmes = sorted(
        key for key in _registered_templates() if not (TEMPLATES_ROOT / key / "README.md").is_file()
    )

    assert not missing_readmes, f"registered template(s) missing README.md: {missing_readmes}"
