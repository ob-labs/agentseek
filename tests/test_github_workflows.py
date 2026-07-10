"""Regression checks for GitHub Actions workflow contracts."""

from __future__ import annotations

from pathlib import Path


def test_phoenix_smoke_verifies_multiple_trace_markers() -> None:
    """The Phoenix smoke job must prove more than one persisted trace."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "export TRACE_COUNT=3" in text
    assert "for index in range(1, trace_count + 1):" in text
    assert "trace_markers.append(trace_name)" in text
    assert "for marker in $(cat /tmp/agentseek-trace-markers.txt); do" in text
    assert "Verified ${verified_count} Phoenix trace markers persisted in OceanBase seekdb." in text


def test_hybrid_template_smoke_runs_rendered_project_tests() -> None:
    """The hybrid template should be tested after rendering, not only by static source checks."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "agentic-rag-hybrid-template-smoke:" in text
    assert "agentseek create langchain/agentic-rag-hybrid --no-input" in text
    assert "uv sync --extra dev" in text
    assert "uv run python -m pytest" in text


def test_hybrid_template_smoke_builds_rendered_frontend() -> None:
    """The hybrid smoke should install and production-build the rendered frontend."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "main.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "cd \"${AGENTSEEK_HYBRID_SMOKE_PROJECT}/frontend\"" in text
    assert "npm install" in text
    assert "npm run build" in text


def test_openvino_template_smoke_is_path_gated_and_invokes_graph() -> None:
    """The heavy OpenVINO smoke should run only for relevant PRs and prove runtime wiring."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "openvino-template-smoke.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "permissions:" in text
    assert "contents: read" in text
    assert "concurrency:" in text
    assert "workflow_dispatch:" in text
    assert "pull_request:" in text
    assert ".github/workflows/openvino-template-smoke.yml" in text
    assert ".github/actions/setup-python-env/**" in text
    assert "pyproject.toml" in text
    assert "uv.lock" in text
    assert "src/agentseek/**" in text
    assert "templates/index.json" in text
    assert "templates/langchain/agentic-rag-openvino/**" in text
    assert "tests/cli_commands/test_templates_render.py" in text
    assert "tests/test_github_workflows.py" in text
    assert "runs-on: ubuntu-latest" in text
    assert "agentseek create langchain/agentic-rag-openvino --no-input" in text
    assert "agentseek task sync" in text
    assert "agentseek task models" in text
    assert "until docker compose exec -T seekdb mysql" in text
    assert "openvino-smoke-fixture.md" in text
    assert "cobalt-lantern-42" in text
    assert "uv run ingest openvino-smoke-fixture.md" in text
    assert "agentseek task ingest-sample" not in text
    assert "lilianweng.github.io" not in text
    assert "agentseek dev --dry-run" in text
    assert "from langchain_core.messages import HumanMessage" in text
    assert "from my_openvino_rag_agent import agent as agent_module" in text
    assert "agent_module.retrieve = verified_retrieve" in text
    assert "retrieval_calls.clear()" in text
    assert "OpenVINO retrieval did not return fixture context" in text
    assert "OpenVINO graph did not call retrieval during sync invoke" in text
    assert "OpenVINO graph did not call retrieval during async invoke" in text
    assert "graph.invoke" in text
    assert "graph.ainvoke" in text
    assert "asyncio.run" in text
    assert "OpenVINO graph returned empty response" in text
    assert "OpenVINO async graph returned empty response" in text
