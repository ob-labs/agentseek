"""Hybrid RAG template-specific render and static checks."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tomllib
import zipfile
from pathlib import Path

import yaml
from cookiecutter.main import cookiecutter
from typer.testing import CliRunner

from tests.cli_commands.helpers import build_command_app

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_DIR = REPO_ROOT / "templates" / "langchain" / "agentic-rag-hybrid"


def test_hybrid_template_contains_expected_custom_runtime_files() -> None:
    project_dir = TEMPLATE_DIR / "{{cookiecutter.project_slug}}"
    lifecycle = project_dir / ".agentseek" / "lifecycle.toml"

    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "routes.py").is_file()
    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "middleware.py").is_file()
    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "observability.py").is_file()
    assert (project_dir / "src" / "{{cookiecutter.project_slug}}" / "retrieval_runnables.py").is_file()
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
    cors = langgraph["http"]["cors"]
    assert cors["allow_origins"] == ["http://127.0.0.1:5175"]
    origin_pattern = cors["allow_origin_regex"]
    assert re.fullmatch(origin_pattern, "http://192.0.2.10:5175")
    assert re.fullmatch(origin_pattern, "https://frontend.example.test:5175")
    assert re.fullmatch(origin_pattern, "http://[2001:db8::1]:5175")
    assert not re.fullmatch(origin_pattern, "https://frontend.example.test:5176")
    assert not re.fullmatch(origin_pattern, "http://[2001:db8::1]:5176")

    frontend_package = json.loads((generated / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert "--host" not in frontend_package["scripts"]["dev"]

    lifecycle = tomllib.loads((generated / ".agentseek" / "lifecycle.toml").read_text(encoding="utf-8"))
    assert lifecycle["template"] == "langchain/agentic-rag-hybrid"
    assert set(lifecycle["processes"]) == {"backend", "frontend"}
    assert lifecycle["services"]["phoenix"]["url"] == "http://127.0.0.1:6006"
    assert lifecycle["services"]["phoenix_seekdb"]["url"] == "mysql://127.0.0.1:2884/phoenix"
    assert lifecycle["checks"]["custom_routes"]["target"] == "http://127.0.0.1:2024/custom/health"
    assert lifecycle["env"]["AGENTSEEK_API_KEY"]["required"] is True
    assert lifecycle["env"]["AGENTSEEK_API_KEY"]["aliases"] == ["SILICONFLOW_API_KEY", "OPENAI_API_KEY"]
    assert "SILICONFLOW_API_KEY" not in lifecycle["env"]
    assert lifecycle["env"]["AGENTSEEK_API_BASE"]["default"] == "https://api.siliconflow.cn/v1"
    assert lifecycle["tasks"]["phoenix"]["command"] == ["docker", "compose", "up", "-d", "phoenix"]
    assert lifecycle["tasks"]["phoenix-stop"]["command"] == ["docker", "compose", "down"]
    assert lifecycle["tasks"]["seekdb-skills"]["command"] == [
        "npx",
        "skills",
        "add",
        "oceanbase/seekdb-ecology-plugins",
        "--all",
    ]


def test_hybrid_template_lifecycle_accepts_canonical_api_key(tmp_path: Path, monkeypatch) -> None:
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    cookiecutter(str(TEMPLATE_DIR), output_dir=str(out_dir), no_input=True)
    generated = out_dir / "my_hybrid_rag_agent"

    (generated / ".env").write_text("AGENTSEEK_API_KEY=test-key\n", encoding="utf-8")
    (generated / "frontend" / "node_modules").mkdir()
    for name in ("AGENTSEEK_API_KEY", "SILICONFLOW_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(generated)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--strict"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "ok   AGENTSEEK_API_KEY:" in result.stdout


def test_hybrid_template_teaches_hybrid_search_modes() -> None:
    project_dir = TEMPLATE_DIR / "{{cookiecutter.project_slug}}"

    guide = (project_dir / "docs" / "hybrid-search-guide.md").read_text(encoding="utf-8")
    lab = (project_dir / "frontend" / "src" / "SampleLab.tsx").read_text(encoding="utf-8")
    middleware = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "middleware.py").read_text(encoding="utf-8")
    routes = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "routes.py").read_text(encoding="utf-8")
    retrieval_runnables = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "retrieval_runnables.py").read_text(
        encoding="utf-8"
    )
    store = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "store.py").read_text(encoding="utf-8")
    agent = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "agent.py").read_text(encoding="utf-8")
    observability = (project_dir / "src" / "{{cookiecutter.project_slug}}" / "observability.py").read_text(
        encoding="utf-8"
    )
    readme = (project_dir / "README.md").read_text(encoding="utf-8")
    env_example = (project_dir / ".env.example").read_text(encoding="utf-8")
    compose = (project_dir / "docker-compose.yml").read_text(encoding="utf-8")
    template_config = json.loads((TEMPLATE_DIR / "cookiecutter.json").read_text(encoding="utf-8"))

    assert "agentseek task seekdb-skills" in readme
    assert "## Agent Skills" in readme
    assert "PR #122" not in readme
    assert '_nonempty_env("AGENTSEEK_API_KEY")' in agent
    assert "HYBRID_AUXILIARY_CANDIDATE_LIMIT" in env_example
    for mode in ("semantic", "keyword", "exact", "balanced"):
        assert mode in guide
        assert mode in middleware
    assert "Index starter pack" in lab
    assert "/custom/sample-pack/ingest" in routes
    assert "/custom/compare" in routes
    assert "/custom/observability" in routes
    assert "compare_modes_runnable" in routes
    assert "RunnableLambda" in retrieval_runnables
    assert "trace_custom_route" not in routes
    assert "trace_custom_route" not in observability
    assert "OceanbaseVectorStore" in store
    assert "import pyseekdb" not in store
    assert "configure_tracing(get_settings())" in agent
    assert "LangChainInstrumentor" in observability
    assert "OTLPSpanExporter" in observability
    assert "AGENTSEEK_API_KEY=" in env_example
    assert "AGENTSEEK_API_BASE=https://api.siliconflow.cn/v1" in env_example
    assert "SEEKDB_PATH={{ cookiecutter.seekdb_path }}" in env_example
    assert "EMBEDDING_BASE_URL=" in env_example
    assert "AGENTSEEK_OTEL_ENABLED=false" in env_example
    assert "AGENTSEEK_PHOENIX_IMAGE=ghcr.io/agentseek-ai/agentseek-phoenix:main" in env_example
    assert "OCEANBASE_SEEKDB_IMAGE=quay.io/oceanbase/seekdb:latest" in env_example
    assert "${AGENTSEEK_PHOENIX_IMAGE:-ghcr.io/agentseek-ai/agentseek-phoenix:main}" in compose
    assert "${OCEANBASE_SEEKDB_IMAGE:-quay.io/oceanbase/seekdb:latest}" in compose
    assert "PHOENIX_SQL_DATABASE_URL: mysql://root@seekdb:2881/phoenix" in compose
    assert template_config["default_model"] == "openai:zai-org/GLM-5.2"
    assert template_config["embedding_model"] == "Qwen/Qwen3-VL-Embedding-8B"
    assert template_config["vlm_model"] == "zai-org/GLM-4.5V"
    assert "Answer in the same language as the user's question." in template_config["system_prompt"]


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
