"""Documentation regression checks for lifecycle task guidance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_ROOT = ROOT / "templates"
TEMPLATE_INDEX = TEMPLATES_ROOT / "index.json"
LIFECYCLE_REFERENCES = (
    ROOT / "docs" / "reference" / "lifecycle-spec.md",
    ROOT / "docs" / "reference" / "lifecycle-spec.zh.md",
)
LIFECYCLE_V2_SPEC_URL = "https://github.com/ob-labs/agentseek/blob/main/specs/lifecycle-v2-service-discovery.md"


def _public_template_readmes() -> list[Path]:
    registry = json.loads(TEMPLATE_INDEX.read_text(encoding="utf-8"))
    readmes: list[Path] = []
    for key in sorted(registry):
        template_dir = TEMPLATES_ROOT / key
        for readme in [
            template_dir / "README.md",
            template_dir / "{{cookiecutter.project_slug}}" / "README.md",
        ]:
            if readme.is_file():
                readmes.append(readme)
    return readmes


def test_quickstarts_prefer_lifecycle_tasks_over_raw_setup_commands() -> None:
    """Public quickstarts should route setup through AgentSeek lifecycle tasks."""
    docs = [
        ROOT / "README.md",
        ROOT / "README.zh.md",
        ROOT / "docs" / "index.md",
        ROOT / "docs" / "index.zh.md",
        ROOT / "docs" / "get-started" / "index.md",
        ROOT / "docs" / "get-started" / "index.zh.md",
        *_public_template_readmes(),
    ]

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        assert "uv sync" not in text, doc
        assert "npm install --prefix frontend" not in text, doc


def test_core_quickstarts_show_lifecycle_task_discovery() -> None:
    """Main quickstarts should show task discovery after project creation."""
    docs = [
        ROOT / "README.md",
        ROOT / "README.zh.md",
        ROOT / "docs" / "index.md",
        ROOT / "docs" / "index.zh.md",
        ROOT / "docs" / "get-started" / "index.md",
        ROOT / "docs" / "get-started" / "index.zh.md",
    ]

    for doc in docs:
        assert "agentseek task" in doc.read_text(encoding="utf-8"), doc


@pytest.mark.parametrize("reference", LIFECYCLE_REFERENCES)
def test_lifecycle_references_describe_authored_v2_loading(reference: Path) -> None:
    """Both references must describe the shipped authored v1/v2 boundary."""
    text = reference.read_text(encoding="utf-8")
    table_rows = [line for line in text.splitlines() if line.startswith("|")]

    assert LIFECYCLE_V2_SPEC_URL in text, reference
    assert "lifecycle-v2-service-discovery.md" in text, reference
    assert any("`1`, `2`" in row for row in table_rows), reference
    assert any("`templates/`" in row and "`version = 1`" in row for row in table_rows), reference
    has_v2_catalog_row = any(
        "`agentseek-ai/agentseek-templates`" in row and "`version = 2`" in row for row in table_rows
    )
    assert has_v2_catalog_row, reference
