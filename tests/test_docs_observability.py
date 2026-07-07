"""Documentation regression checks for observability guarantees."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_observability_guides_do_not_include_ci_proof_details() -> None:
    """Guides should stay user-facing and omit internal CI proof details."""
    guides = [
        ROOT / "docs" / "guides" / "observability-tracing.md",
        ROOT / "docs" / "guides" / "observability-tracing.zh.md",
    ]

    for guide in guides:
        text = guide.read_text(encoding="utf-8")
        assert "OceanBase seekdb" in text, guide
        assert "agentseek-phoenix-compose" not in text, guide
        assert "trace marker" not in text.lower(), guide


def test_template_docs_describe_multiple_phoenix_trace_proof() -> None:
    """Template docs should explain the CI proof behind Phoenix on OceanBase seekdb."""
    docs = [
        ROOT / "templates" / "langchain" / "default" / "README.md",
        ROOT / "templates" / "langchain" / "default" / "{{cookiecutter.project_slug}}" / "README.md",
    ]

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        assert "OceanBase seekdb" in text, doc
        assert "three" in text.lower() or "3" in text, doc
        assert "trace marker" in text.lower(), doc
        assert "agentseek-phoenix-compose" in text, doc
