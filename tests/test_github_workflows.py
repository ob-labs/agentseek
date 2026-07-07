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
