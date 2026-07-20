"""Regression checks for repository-owned skills."""

from __future__ import annotations

import codecs
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
LANGCHAIN_GUIDE_ROOT = SKILLS_ROOT / "langchain-dev-guide"
STRUCTURED_OUTPUT_GUIDE = LANGCHAIN_GUIDE_ROOT / "reference" / "structured-output.md"


def test_skill_markdown_files_are_utf8_without_bom() -> None:
    """Skill metadata and headings must start at the first byte."""
    files_with_bom = [
        path.relative_to(ROOT)
        for path in sorted(SKILLS_ROOT.rglob("*.md"))
        if path.read_bytes().startswith(codecs.BOM_UTF8)
    ]

    assert not files_with_bom, files_with_bom


def test_langchain_guide_uses_current_deepseek_v4_model() -> None:
    """Troubleshooting examples should not use a retiring model alias."""
    guide = STRUCTURED_OUTPUT_GUIDE.read_text(encoding="utf-8")

    assert 'model="deepseek-reasoner"' not in guide
    assert 'model="deepseek-v4-flash"' in guide
    assert 'extra_body={"thinking": {"type": "enabled"}}' in guide


def test_structured_output_guide_distinguishes_model_and_agent_apis() -> None:
    """Model wrappers and agents must use their actual structured-output APIs."""
    guide = STRUCTURED_OUTPUT_GUIDE.read_text(encoding="utf-8")

    assert "ProviderStrategy" in guide
    assert "ToolStrategy" in guide
    assert "model.bind_tools([schema_tool]" not in guide


def test_structured_output_guide_explains_when_models_can_skip_schema_tools() -> None:
    """Skipping a schema tool is possible only after forced selection is removed."""
    guide = STRUCTURED_OUTPUT_GUIDE.read_text(encoding="utf-8")

    assert "forces the schema tool" in guide
    assert "free to skip the schema tool" in guide
