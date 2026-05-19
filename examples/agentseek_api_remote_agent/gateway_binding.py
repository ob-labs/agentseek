"""Connect agentseek to a remote agentseek-api runtime."""

from __future__ import annotations

from typing import Any

from agentseek_langchain import LangGraphClientRunnable, RunnableSpec, default_runnable_config
from agentseek_langchain.ag_ui import langchain_messages_from_state
from agentseek_langchain.profiles import parse_messages_output
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph_sdk import get_client, get_sync_client

from .settings import AgentSeekApiRemoteExampleSettings, get_agentseek_api_remote_settings


def _build_remote_input(context) -> dict[str, Any]:
    messages = langchain_messages_from_state(context.state)
    if not messages:
        messages = [HumanMessage(content=context.prompt)]
    if context.agents_md:
        messages = [SystemMessage(content=context.agents_md), *messages]
    return {"messages": messages}


def _resolve_assistant_id(settings: AgentSeekApiRemoteExampleSettings) -> str:
    explicit_id = settings.assistant_id.strip()
    if explicit_id:
        return explicit_id

    headers = settings.request_headers()
    with get_sync_client(url=settings.api_url, headers=headers) as client:
        assistants = client.assistants.search(
            name=settings.assistant_name,
            graph_id=settings.graph_id,
            limit=1,
        )
        if assistants:
            return str(assistants[0]["assistant_id"])

        created = client.assistants.create(
            graph_id=settings.graph_id,
            name=settings.assistant_name,
            metadata={"source": "examples.agentseek_api_remote_agent"},
        )
        return str(created["assistant_id"])


def build_spec() -> RunnableSpec:
    """Return a RunnableSpec backed by a remote agentseek-api runtime."""

    settings = get_agentseek_api_remote_settings()
    client = get_client(url=settings.api_url, headers=settings.request_headers())
    runnable = LangGraphClientRunnable(
        client,
        assistant_id=_resolve_assistant_id(settings),
        thread_on_session=settings.thread_on_session,
    )
    return RunnableSpec(
        runnable=runnable,
        build_input=_build_remote_input,
        parse_output=parse_messages_output,
        build_config=default_runnable_config,
    )
