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


class _LazyCreateAgent:
    """Defer `create_agent` until first `ainvoke` so missing API keys do not break import."""

    __slots__ = ("_compiled",)

    def __init__(self) -> None:
        self._compiled: Any = None

    def _graph(self) -> Any:
        if self._compiled is None:
            settings = get_ag_ui_langchain_demo_settings()
            model = settings.model.strip()
            if not model:
                msg = "Set AGENTSEEK_MODEL (e.g. openai:gpt-4o-mini) for the LangChain demo agent."
                raise RuntimeError(msg)
            settings.apply_openai_env_bridge()
            self._compiled = create_agent(
                model=model,
                tools=[],
                middleware=[
                    normalize_context,
                    CopilotKitMiddleware(),
                    apply_structured_output_schema,
                ],
                context_schema=AgentContext,
                state_schema=AgentState,
                system_prompt=(
                    "You are a helpful UI assistant. Build visual responses using the available components."
                ),
            )
        return self._compiled

    async def ainvoke(self, runnable_input: object, config: Any = None) -> object:
        if config is not None:
            return await self._graph().ainvoke(runnable_input, config=config)
        return await self._graph().ainvoke(runnable_input)


def build_spec():
    """Return a `RunnableSpec` (``BUB_LANGCHAIN_SPEC`` / ``AGENTSEEK_LANGCHAIN_SPEC``)."""
    return messages_spec(_LazyCreateAgent(), include_agents_md=True)
