"""LangChain `create_agent` with CopilotKit middleware, driven through AgentSeek.

Same agent shape as LangChain's CopilotKit + LangGraph guide, but the runnable is
loaded via `agentseek-langchain` (`messages_spec`) instead of FastAPI +
`add_langgraph_fastapi_endpoint`.

See: https://docs.langchain.com/oss/python/langchain/frontend/integrations/copilotkit
"""

from __future__ import annotations

from typing import Any, TypedDict

from agentseek_langchain import messages_spec
from copilotkit import CopilotKitMiddleware, CopilotKitState
from langchain.agents import create_agent

from ag_ui_langchain.middleware import apply_structured_output_schema, normalize_context
from ag_ui_langchain.settings import get_ag_ui_langchain_demo_settings


class AgentState(CopilotKitState):
    pass


class AgentContext(TypedDict, total=False):
    output_schema: dict[str, Any]


def build_agent() -> Any:
    """Build the guide-aligned LangChain agent.

    The agent definition intentionally stays close to the LangChain CopilotKit
    docs. AgentSeek-specific transport concerns live outside this function.
    """

    settings = get_ag_ui_langchain_demo_settings()
    model = settings.model.strip()
    if not model:
        msg = "Set AGENTSEEK_MODEL (e.g. openai:gpt-4o-mini) for the LangChain demo agent."
        raise RuntimeError(msg)
    settings.apply_openai_env_bridge()
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
        system_prompt=("You are a helpful UI assistant. Build visual responses using the available components."),
    )


class _LazyAgentRunnable:
    """Defer agent creation until first `ainvoke` so imports stay lightweight."""

    __slots__ = ("_compiled",)

    def __init__(self) -> None:
        self._compiled: Any = None

    def _agent(self) -> Any:
        if self._compiled is None:
            self._compiled = build_agent()
        return self._compiled

    async def ainvoke(self, runnable_input: object, config: Any = None, context: Any = None) -> object:
        kwargs: dict[str, Any] = {}
        if config is not None:
            kwargs["config"] = config
        if context is not None:
            kwargs["context"] = context
        return await self._agent().ainvoke(runnable_input, **kwargs)


def build_spec():
    """Return a `RunnableSpec` (``BUB_LANGCHAIN_SPEC`` / ``AGENTSEEK_LANGCHAIN_SPEC``)."""
    return messages_spec(_LazyAgentRunnable(), include_agents_md=True)
