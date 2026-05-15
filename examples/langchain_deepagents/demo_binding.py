"""Expose a local DeepAgents runnable to agentseek."""

from __future__ import annotations

from typing import Any

from agentseek_langchain import messages_spec
from deepagents import create_deep_agent

from .settings import get_deepagents_example_settings


def outline_answer(topic: str) -> str:
    """Return a lightweight response outline for planning-heavy prompts."""

    cleaned = topic.strip()
    if not cleaned:
        return "No topic provided."
    return (
        f"Suggested outline for {cleaned}:\n"
        "1. State the goal in one sentence.\n"
        "2. List the main constraints and tradeoffs.\n"
        "3. Finish with recommended next steps."
    )


def build_agent() -> Any:
    """Build a local DeepAgents runnable."""

    settings = get_deepagents_example_settings()
    settings.apply_openai_env_bridge()
    return create_deep_agent(
        model=settings.require_model(),
        tools=[outline_answer],
        system_prompt=(
            "You are a pragmatic engineering assistant. "
            "Use the outline_answer tool when a planning scaffold would help, "
            "but answer directly when the user request is already precise."
        ),
    )


def build_spec():
    """Return a RunnableSpec for AGENTSEEK_LANGCHAIN_SPEC."""

    return messages_spec(build_agent(), include_agents_md=True)
