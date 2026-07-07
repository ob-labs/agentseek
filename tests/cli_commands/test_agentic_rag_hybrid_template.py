"""Hybrid RAG template-specific render and static checks."""

from __future__ import annotations

import json
import shutil
import subprocess
import tomllib
from pathlib import Path

from cookiecutter.main import cookiecutter

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "templates" / "langchain" / "agentic-rag-hybrid"


def test_hybrid_template_contains_expected_custom_runtime_files() -> None:
    project_dir = TEMPLATE_DIR / "{{cookiecutter.project_slug}}"
    lifecycle = project_dir / ".agentseek" / "lifecycle.toml"

    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "routes.py").is_file()
    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "middleware.py").is_file()
    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "sample_pack.py").is_file()
    assert (project_dir / "frontend" / "src" / "SampleLab.tsx").is_file()
    assert (project_dir / "examples" / "sample_pack" / "sample_pack.zip").is_file()
    assert lifecycle.is_file()
    git = shutil.which("git")
    assert git is not None
    subprocess.run(  # noqa: S603
        [git, "ls-files", "--error-unmatch", str(lifecycle.relative_to(REPO_ROOT))],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_hybrid_template_langgraph_http_app_contract(tmp_path: Path) -> None:
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    cookiecutter(str(TEMPLATE_DIR), output_dir=str(out_dir), no_input=True)
    generated = out_dir / "my_hybrid_rag_agent"

    langgraph = json.loads((generated / "langgraph.json").read_text(encoding="utf-8"))
    assert langgraph["graphs"]["hybrid-rag"] == "./src/my_hybrid_rag_agent/agent.py:graph"
    assert langgraph["http"]["app"] == "./src/my_hybrid_rag_agent/routes.py:app"
    assert langgraph["http"]["middleware_order"] == "middleware_first"

    lifecycle = tomllib.loads((generated / ".agentseek" / "lifecycle.toml").read_text(encoding="utf-8"))
    assert lifecycle["template"] == "langchain/agentic-rag-hybrid"
    assert set(lifecycle["processes"]) == {"seekdb", "backend", "frontend"}
    assert lifecycle["checks"]["custom_routes"]["target"] == "http://127.0.0.1:2024/custom/health"


def test_hybrid_template_teaches_hybrid_search_modes() -> None:
    project_dir = TEMPLATE_DIR / "{{cookiecutter.project_slug}}"

    guide = (project_dir / "docs" / "hybrid-search-guide.md").read_text(encoding="utf-8")
    lab = (project_dir / "frontend" / "src" / "SampleLab.tsx").read_text(encoding="utf-8")
    middleware = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "middleware.py").read_text(encoding="utf-8")
    routes = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "routes.py").read_text(encoding="utf-8")

    for mode in ("semantic", "keyword", "exact", "balanced"):
        assert mode in guide
        assert mode in middleware
    assert "Index starter pack" in lab
    assert "/custom/sample-pack/ingest" in routes
    assert "/custom/compare" in routes
