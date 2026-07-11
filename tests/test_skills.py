"""Regression checks for repository-owned skills."""

from __future__ import annotations

import codecs
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"


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
    guide = (
        SKILLS_ROOT / "langchain-dev-guide" / "reference" / "common-issues.md"
    ).read_text(encoding="utf-8")

    assert 'model="deepseek-reasoner"' not in guide
    assert 'model="deepseek-v4-flash"' in guide
    assert 'extra_body={"thinking": {"type": "enabled"}}' in guide
