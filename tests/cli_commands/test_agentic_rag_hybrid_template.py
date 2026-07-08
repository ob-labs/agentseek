"""Hybrid RAG template-specific render and static checks."""

from __future__ import annotations

import json
import shutil
import subprocess
import tomllib
import zipfile
from pathlib import Path

import yaml
from cookiecutter.main import cookiecutter

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "templates" / "langchain" / "agentic-rag-hybrid"


def test_hybrid_template_contains_expected_custom_runtime_files() -> None:
    project_dir = TEMPLATE_DIR / "{{cookiecutter.project_slug}}"
    lifecycle = project_dir / ".agentseek" / "lifecycle.toml"

    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "routes.py").is_file()
    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "middleware.py").is_file()
    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "observability.py").is_file()
    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "sample_pack.py").is_file()
    assert (project_dir / "frontend" / "src" / "SampleLab.tsx").is_file()
    assert (project_dir / "examples" / "sample_pack" / "sample_pack.zip").is_file()
    assert (project_dir / "docker-compose.yml").is_file()
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
    assert langgraph["graphs"]["hybrid-rag"] == "my_hybrid_rag_agent.agent:graph"
    assert langgraph["http"]["app"] == "my_hybrid_rag_agent.routes:app"
    assert langgraph["http"]["middleware_order"] == "middleware_first"

    lifecycle = tomllib.loads((generated / ".agentseek" / "lifecycle.toml").read_text(encoding="utf-8"))
    assert lifecycle["template"] == "langchain/agentic-rag-hybrid"
    assert set(lifecycle["processes"]) == {"backend", "frontend"}
    assert lifecycle["services"]["phoenix"]["url"] == "http://127.0.0.1:6006"
    assert lifecycle["services"]["phoenix_seekdb"]["url"] == "mysql://127.0.0.1:2884/phoenix"
    assert lifecycle["checks"]["custom_routes"]["target"] == "http://127.0.0.1:2024/custom/health"
    assert lifecycle["tasks"]["phoenix"]["command"] == ["docker", "compose", "up", "-d", "phoenix"]
    assert lifecycle["tasks"]["phoenix-stop"]["command"] == ["docker", "compose", "down"]


def test_hybrid_template_teaches_hybrid_search_modes() -> None:
    project_dir = TEMPLATE_DIR / "{{cookiecutter.project_slug}}"

    guide = (project_dir / "docs" / "hybrid-search-guide.md").read_text(encoding="utf-8")
    lab = (project_dir / "frontend" / "src" / "SampleLab.tsx").read_text(encoding="utf-8")
    middleware = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "middleware.py").read_text(encoding="utf-8")
    routes = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "routes.py").read_text(encoding="utf-8")
    store = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "store.py").read_text(encoding="utf-8")
    agent = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "agent.py").read_text(encoding="utf-8")
    observability = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "observability.py").read_text(
        encoding="utf-8"
    )
    env_example = (project_dir / ".env.example").read_text(encoding="utf-8")
    compose = (project_dir / "docker-compose.yml").read_text(encoding="utf-8")
    template_config = json.loads((TEMPLATE_DIR / "cookiecutter.json").read_text(encoding="utf-8"))

    for mode in ("semantic", "keyword", "exact", "balanced"):
        assert mode in guide
        assert mode in middleware
    assert "Index starter pack" in lab
    assert "/custom/sample-pack/ingest" in routes
    assert "/custom/compare" in routes
    assert "/custom/observability" in routes
    assert "OceanbaseVectorStore" in store
    assert "import pyseekdb" not in store
    assert "configure_tracing(get_settings())" in agent
    assert "LangChainInstrumentor" in observability
    assert "OTLPSpanExporter" in observability
    assert "SILICONFLOW_API_KEY" in env_example
    assert "SEEKDB_PATH={{ cookiecutter.seekdb_path }}" in env_example
    assert "EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1" in env_example
    assert "AGENTSEEK_OTEL_ENABLED=false" in env_example
    assert "AGENTSEEK_PHOENIX_IMAGE=ghcr.io/agentseek-ai/agentseek-phoenix:main" in env_example
    assert "OCEANBASE_SEEKDB_IMAGE=quay.io/oceanbase/seekdb:latest" in env_example
    assert "${AGENTSEEK_PHOENIX_IMAGE:-ghcr.io/agentseek-ai/agentseek-phoenix:main}" in compose
    assert "${OCEANBASE_SEEKDB_IMAGE:-quay.io/oceanbase/seekdb:latest}" in compose
    assert "PHOENIX_SQL_DATABASE_URL: mysql://root@seekdb:2881/phoenix" in compose
    assert template_config["default_model"] == "openai:zai-org/GLM-5.2"
    assert template_config["embedding_model"] == "Qwen/Qwen3-VL-Embedding-8B"
    assert template_config["vlm_model"] == "zai-org/GLM-4.5V"


def test_hybrid_template_sample_cases_explain_mode_specific_winners() -> None:
    project_dir = TEMPLATE_DIR / "{{cookiecutter.project_slug}}"
    manifest = yaml.safe_load((project_dir / "examples" / "sample_pack" / "manifest.yml").read_text(encoding="utf-8"))
    case_data = yaml.safe_load((project_dir / "examples" / "hybrid_cases.yml").read_text(encoding="utf-8"))
    image_ids = {item["id"] for item in manifest["images"]}
    modes = {"semantic", "keyword", "exact", "balanced"}

    for case in case_data["cases"]:
        winners = case["expected_top_by_mode"]
        assert set(winners) == modes
        assert set(winners.values()).issubset(image_ids)
        assert len(set(winners.values())) >= 2


def test_hybrid_template_sample_pack_zip_matches_manifest() -> None:
    project_dir = TEMPLATE_DIR / "{{cookiecutter.project_slug}}"
    manifest = yaml.safe_load((project_dir / "examples" / "sample_pack" / "manifest.yml").read_text(encoding="utf-8"))
    image_dir = project_dir / "examples" / "sample_pack" / "images"
    with zipfile.ZipFile(project_dir / "examples" / "sample_pack" / "sample_pack.zip") as archive:
        names = set(archive.namelist())
        zipped_images = {
            name.removeprefix("images/"): archive.read(name) for name in names if name.startswith("images/")
        }

    assert "manifest.yml" in names
    for item in manifest["images"]:
        assert f"images/{item['file_name']}" in names
        image_bytes = (image_dir / item["file_name"]).read_bytes()
        assert image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        assert zipped_images[item["file_name"]] == image_bytes
