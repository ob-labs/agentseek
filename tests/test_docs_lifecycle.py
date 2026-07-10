"""Documentation regression checks for lifecycle task guidance."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_ROOT = ROOT / "templates"
TEMPLATE_INDEX = TEMPLATES_ROOT / "index.json"


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
