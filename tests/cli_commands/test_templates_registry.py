"""Registry consistency checks for bundled cookiecutter templates."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_ROOT = REPO_ROOT / "templates"
INDEX_PATH = TEMPLATES_ROOT / "index.json"
EXPECTED_TEMPLATE_KEYS = {
    "bub/default",
    "deepagents/content-builder",
    "deepagents/default",
    "deepagents/ragflow-knowledge-qa",
    "deepagents/research",
    "langchain/agentic-rag",
    "langchain/agentic-rag-openvino",
    "langchain/cli-remote",
    "langchain/default",
    "langchain/markdown-messages",
    "langchain/sandbox",
}
QUARANTINED_TEMPLATE_KEYS = {
    "bub/contextseek",
}


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
    missing = sorted(_template_dirs() - _registered_templates() - QUARANTINED_TEMPLATE_KEYS)

    assert not missing, f"template(s) missing from templates/index.json: {missing}"


def test_registry_contains_expected_template_keys() -> None:
    """The shared registry advertises the template set published from main."""
    missing = sorted(EXPECTED_TEMPLATE_KEYS - _registered_templates())

    assert not missing, f"templates/index.json missing expected key(s): {missing}"


def test_contextseek_template_is_not_advertised_until_dev_locking_is_resolved() -> None:
    """Do not offer bub/contextseek while its embedded store can be double-opened by dev."""
    assert "bub/contextseek" in QUARANTINED_TEMPLATE_KEYS
    assert "bub/contextseek" not in _registered_templates()


def test_registered_templates_have_readme() -> None:
    """Every currently checked-out registered template has a top-level README."""
    missing_readmes = sorted(
        key for key in _template_dirs() & _registered_templates() if not (TEMPLATES_ROOT / key / "README.md").is_file()
    )

    assert not missing_readmes, f"registered template(s) missing README.md: {missing_readmes}"


def test_ragflow_template_has_required_source_structure() -> None:
    """The RAGFlow contribution follows the bundled-template source contract."""
    template_root = TEMPLATES_ROOT / "deepagents" / "ragflow-knowledge-qa"
    generated_root = template_root / "{{cookiecutter.project_slug}}"

    required = {
        template_root / "cookiecutter.json",
        template_root / "README.md",
        generated_root / ".agentseek" / "lifecycle.toml",
        generated_root / ".env.example",
        generated_root / "README.md",
        generated_root / "pyproject.toml",
        generated_root / "uploads" / "sample-policy.md",
    }

    missing = sorted(str(path.relative_to(TEMPLATES_ROOT)) for path in required if not path.is_file())
    assert not missing, f"RAGFlow template missing required source files: {missing}"
