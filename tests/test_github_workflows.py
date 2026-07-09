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


def test_openvino_template_smoke_is_manual_linux_workflow() -> None:
    """The heavy OpenVINO smoke should be available on Linux without gating every PR."""
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "openvino-template-smoke.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "runs-on: ubuntu-latest" in text
    assert "agentseek create langchain/agentic-rag-openvino --no-input" in text
    assert "agentseek task models" in text
    assert "agentseek task ingest-sample" in text
    assert "agentseek dev --dry-run" in text
