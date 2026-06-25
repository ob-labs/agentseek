"""LangChain `create_agent` with CopilotKit middleware, driven through Bub."""

from __future__ import annotations

from typing import Any, TypedDict

from agentseek_langchain import messages_spec
from copilotkit import CopilotKitMiddleware, CopilotKitState
from langchain.agents import create_agent

from .middleware import apply_structured_output_schema, normalize_context
from .observability import configure_tracing
from .settings import get_settings


class AgentState(CopilotKitState):
    pass


class AgentContext(TypedDict, total=False):
    output_schema: dict[str, Any]


def build_agent() -> Any:
    """Build the agent runnable."""

    settings = get_settings()
    model = settings.model.strip()
    if not model:
        msg = "Set BUB_MODEL (e.g. openai:gpt-4o-mini) for the {{ cookiecutter.project_name }} agent."
        raise RuntimeError(msg)
    settings.apply_openai_env_bridge()
    configure_tracing(settings)
    return create_agent(
        model=model,
        tools=[],
        middleware=[
            normalize_context,
            CopilotKitMiddleware(),
            apply_structured_output_schema,
        ],
        context_schema=AgentContext,
        state_schema=AgentState,
        system_prompt={{ '"' }}{{ cookiecutter.system_prompt }}{{ '"' }},
    )


def build_spec():
    """Return a `RunnableSpec` for ``BUB_LANGCHAIN_SPEC``."""
    return messages_spec(build_agent(), include_agents_md=True)
