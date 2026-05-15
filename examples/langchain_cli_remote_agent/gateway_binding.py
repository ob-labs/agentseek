"""Connect agentseek to a remote LangGraph CLI agent."""

from __future__ import annotations

from typing import Any

from agentseek_langchain import LangGraphClientRunnable, RunnableSpec, default_runnable_config
from agentseek_langchain.ag_ui import langchain_messages_from_state
from agentseek_langchain.profiles import parse_messages_output
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph_sdk import get_client

from .settings import get_langgraph_cli_remote_settings


def _build_remote_input(context) -> dict[str, Any]:
    messages = langchain_messages_from_state(context.state)
    if not messages:
        messages = [HumanMessage(content=context.prompt)]
    if context.agents_md:
        messages = [SystemMessage(content=context.agents_md), *messages]
    return {"messages": messages}


def build_spec():
    """Return a RunnableSpec backed by a remote LangGraph Agent Server."""

    settings = get_langgraph_cli_remote_settings()
    client = get_client(url=settings.langgraph_url)
    runnable = LangGraphClientRunnable(
        client,
        assistant_id=settings.assistant_id,
        thread_on_session=settings.thread_on_session,
    )
    return RunnableSpec(
        runnable=runnable,
        build_input=_build_remote_input,
        parse_output=parse_messages_output,
        build_config=default_runnable_config,
    )
