"""Documentation regression checks for canonical template paths."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SANDBOX_DOCS = (
    ROOT / "docs" / "guides" / "choose-template.md",
    ROOT / "docs" / "guides" / "choose-template.zh.md",
    ROOT / "docs" / "reference" / "templates.md",
    ROOT / "docs" / "reference" / "templates.zh.md",
    ROOT / "docs" / "guides" / "observability-tracing.md",
    ROOT / "docs" / "guides" / "observability-tracing.zh.md",
)


def test_sandbox_docs_use_canonical_deepagents_path() -> None:
    stale_docs = [
        path.relative_to(ROOT).as_posix()
        for path in SANDBOX_DOCS
        if "langchain/sandbox" in path.read_text(encoding="utf-8")
    ]

    assert not stale_docs, f"docs still reference langchain/sandbox: {stale_docs}"
