from __future__ import annotations

import asyncio
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from agentseek_langchain import LangGraphClientRunnable, messages_spec
from agentseek_langchain.spec import InvocationContext


class _Runs:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls: list[dict[str, Any]] = []

    async def wait(
        self,
        thread_id: str | None,
        assistant_id: str,
        *,
        runnable_input: object | None = None,
        metadata: Mapping[str, Any] | None = None,
        config: Mapping[str, Any] | None = None,
        if_not_exists: str | None = None,
        **kwargs: object,
    ) -> object:
        self.calls.append({
            "thread_id": thread_id,
            "assistant_id": assistant_id,
            "input": runnable_input,
            "metadata": metadata,
            "config": config,
            "if_not_exists": if_not_exists,
            "kwargs": kwargs,
        })
        return self.result


class _Client:
    def __init__(self, result: object) -> None:
        self.runs = _Runs(result)


def test_langgraph_client_runnable_uses_thread_and_metadata(tmp_path: Path) -> None:
    client = _Client({"messages": [{"content": "remote-output"}]})
    runnable = LangGraphClientRunnable(client, assistant_id="agent")
    spec = messages_spec(runnable, include_agents_md=True)
    context = InvocationContext(
        prompt="hello",
        session_id="session-1",
        state={},
        workspace=tmp_path,
        agents_md="rules",
    )

    result = asyncio.run(spec.invoke(context))

    assert result == "remote-output"
    call = client.runs.calls[0]
    assert call["thread_id"] == "session-1"
    assert call["assistant_id"] == "agent"
    assert call["if_not_exists"] == "create"
    assert call["metadata"] == {
        "session_id": "session-1",
        "workspace": str(tmp_path),
    }
    assert call["config"] is None


def test_langgraph_client_runnable_passes_remaining_configurable_fields() -> None:
    client = _Client({"messages": [{"content": "ok"}]})
    runnable = LangGraphClientRunnable(client, assistant_id="agent")

    result = asyncio.run(
        runnable.ainvoke(
            {"messages": []},
            config={
                "metadata": {"source": "test"},
                "configurable": {
                    "thread_id": "thread-1",
                    "session_id": "session-1",
                    "user_id": "u-1",
                },
            },
        )
    )

    assert result == {"messages": [{"content": "ok"}]}
    call = client.runs.calls[0]
    assert call["thread_id"] == "thread-1"
    assert call["metadata"] == {"source": "test"}
    assert call["config"] == {"user_id": "u-1"}


def test_langgraph_client_runnable_can_run_stateless() -> None:
    client = _Client({"messages": [{"content": "ok"}]})
    runnable = LangGraphClientRunnable(client, assistant_id="agent", thread_on_session=False)

    asyncio.run(runnable.ainvoke({"messages": []}, config={"configurable": {"thread_id": "ignored"}}))

    call = client.runs.calls[0]
    assert call["thread_id"] is None
    assert call["if_not_exists"] is None
