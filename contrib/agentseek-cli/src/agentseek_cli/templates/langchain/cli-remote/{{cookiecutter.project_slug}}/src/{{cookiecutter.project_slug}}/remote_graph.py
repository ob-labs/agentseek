"""Graph exported to `langgraph dev` for the remote-agent project."""

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent

try:
    from .settings import get_settings
except ImportError:
    from settings import get_settings  # type: ignore[no-redef]


def rollout_steps(task: str) -> str:
    """Return a concise execution checklist for the requested task."""

    cleaned = task.strip()
    if not cleaned:
        return "No task provided."
    return (
        f"Execution checklist for {cleaned}:\n"
        "1. Restate the desired outcome.\n"
        "2. Name the main risk.\n"
        "3. Propose the next concrete action."
    )


def build_graph() -> Any:
    """Build the remote graph served by `langgraph dev`."""

    settings = get_settings()
    settings.apply_openai_env_bridge()
    return create_agent(
        model=settings.require_model(),
        tools=[rollout_steps],
        system_prompt=(
            "You are a remote LangChain agent running behind LangGraph Agent Server. "
            "Use rollout_steps when a short execution scaffold would help."
        ),
    )


graph = build_graph()
