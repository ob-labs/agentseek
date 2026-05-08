from __future__ import annotations

import asyncio
import importlib
from pathlib import Path
from typing import Any

import pytest
from agentseek_langchain.agent_protocol import (
    AgentProtocolInterruptedError,
    AgentProtocolRemoteError,
    AgentProtocolRunnable,
    AgentProtocolSettings,
)
from agentseek_langchain.bridge import LangchainRunContext
from langchain_core.runnables import Runnable


class _FakeRunsClient:
    def __init__(self, *, wait_response: Any, stream_parts: list[Any]) -> None:
        self.wait_calls: list[dict[str, Any]] = []
        self.stream_calls: list[dict[str, Any]] = []
        self._wait_response = wait_response
        self._stream_parts = list(stream_parts)

    async def wait(self, **kwargs: Any) -> Any:
        self.wait_calls.append(kwargs)
        return self._wait_response

    async def stream(self, **kwargs: Any):
        self.stream_calls.append(kwargs)
        for part in self._stream_parts:
            yield part


class _FakeClient:
    def __init__(self, *, wait_response: Any, stream_parts: list[Any]) -> None:
        self.runs = _FakeRunsClient(wait_response=wait_response, stream_parts=stream_parts)


def _run_context() -> LangchainRunContext:
    return LangchainRunContext(
        session_id="session-1",
        tape_name="tape-x",
        run_id="langchain-run-1",
    )


def _remote_agent_protocol_example():
    return importlib.import_module("remote_agent_protocol")


def _runnable(
    *,
    wait_response: Any = None,
    stream_parts: list[Any] | None = None,
    stateful: bool = False,
    session_id: str | None = None,
) -> tuple[AgentProtocolRunnable, _FakeClient]:
    fake_client = _FakeClient(
        wait_response=wait_response,
        stream_parts=stream_parts or [],
    )
    runnable = AgentProtocolRunnable(
        settings=AgentProtocolSettings(url="http://remote", agent_id="agent", stateful=stateful),
        session_id=session_id,
        langchain_context=_run_context(),
    )
    runnable._client = fake_client
    return runnable, fake_client


def _collect_stream(runnable: AgentProtocolRunnable, value: Any = "hello") -> list[str]:
    async def _collect() -> list[str]:
        return [chunk async for chunk in runnable.astream(value)]

    return asyncio.run(_collect())


def test_agent_protocol_runnable_is_langchain_compatible() -> None:
    runnable = AgentProtocolRunnable(
        settings=AgentProtocolSettings(url="http://example.com", agent_id="agent"),
        session_id="session-1",
        langchain_context=_run_context(),
    )

    assert isinstance(runnable, Runnable)
    assert callable(runnable.invoke)
    assert callable(runnable.ainvoke)
    assert callable(runnable.astream)


def test_ainvoke_uses_deterministic_thread_id_for_stateful_sessions() -> None:
    runnable, fake_client = _runnable(
        wait_response={"messages": [{"role": "assistant", "content": "remote answer"}]},
        session_id="session-1",
        stateful=True,
    )

    first = asyncio.run(runnable.ainvoke("hello"))
    second = asyncio.run(runnable.ainvoke("again"))

    assert first["messages"][-1]["content"] == "remote answer"
    assert second["messages"][-1]["content"] == "remote answer"
    assert len(fake_client.runs.wait_calls) == 2
    first_call = fake_client.runs.wait_calls[0]
    second_call = fake_client.runs.wait_calls[1]
    assert first_call["assistant_id"] == "agent"
    assert first_call["input"] == {"messages": [{"role": "user", "content": "hello"}]}
    assert first_call["if_not_exists"] == "create"
    assert first_call["thread_id"].startswith("agentseek-")
    assert second_call["thread_id"] == first_call["thread_id"]


def test_ainvoke_passes_dict_input_through() -> None:
    runnable, fake_client = _runnable(wait_response={"ok": True})

    payload = {"messages": [{"role": "user", "content": "hi"}], "context": {"mode": "fast"}}
    asyncio.run(runnable.ainvoke(payload))

    assert fake_client.runs.wait_calls[0]["thread_id"] is None
    assert fake_client.runs.wait_calls[0]["input"] == payload
    assert fake_client.runs.wait_calls[0]["if_not_exists"] is None


def test_ainvoke_merges_config_metadata() -> None:
    runnable, fake_client = _runnable(wait_response={"ok": True})

    asyncio.run(runnable.ainvoke("hello", config={"metadata": {"source": "test"}}))

    assert fake_client.runs.wait_calls[0]["metadata"] == {
        "session_id": "session-1",
        "langchain_run_id": "langchain-run-1",
        "tape_name": "tape-x",
        "source": "test",
    }


def test_astream_yields_assistant_message_chunks() -> None:
    runnable, fake_client = _runnable(
        stream_parts=[
            {"event": "messages/partial", "data": [{"type": "human", "content": "hello"}]},
            {"event": "messages/partial", "data": [{"type": "ai", "content": "Hel"}]},
            {"event": "messages/partial", "data": [{"type": "ai", "content": "lo"}]},
            {"event": "values", "data": {"messages": [{"type": "ai", "content": "Hello"}]}},
        ],
    )
    chunks = _collect_stream(runnable)

    assert chunks == ["Hel", "lo"]
    assert fake_client.runs.stream_calls[0]["stream_mode"] == ["messages", "values", "updates"]
    assert "version" not in fake_client.runs.stream_calls[0]


def test_astream_does_not_duplicate_complete_message_after_partials() -> None:
    runnable, _ = _runnable(
        stream_parts=[
            {"event": "messages/partial", "data": [{"type": "ai", "content": "Hel"}]},
            {"event": "messages/partial", "data": [{"type": "ai", "content": "lo"}]},
            {"event": "messages/complete", "data": [{"type": "ai", "content": "Hello"}]},
        ],
    )
    assert _collect_stream(runnable) == ["Hel", "lo"]


def test_astream_falls_back_to_final_state_when_no_message_chunks() -> None:
    runnable, _ = _runnable(
        stream_parts=[
            {"event": "values", "data": {"messages": [{"type": "ai", "content": "Final answer"}]}},
        ],
    )
    chunks = _collect_stream(runnable)

    assert chunks == ["Final answer"]


def test_astream_raises_on_remote_error_event() -> None:
    runnable, _ = _runnable(
        stream_parts=[
            {"event": "error", "data": {"message": "boom"}},
        ],
    )
    with pytest.raises(AgentProtocolRemoteError, match="boom"):
        _collect_stream(runnable)


def test_astream_raises_on_interrupt_update_event() -> None:
    runnable, _ = _runnable(
        stream_parts=[
            {"event": "updates", "data": {"__interrupt__": [{"value": "wait"}]}},
        ],
    )
    with pytest.raises(AgentProtocolInterruptedError, match="interrupted"):
        _collect_stream(runnable)


def test_remote_example_factory_uses_prompt_and_request_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from agentseek_langchain.bridge import LangchainFactoryRequest

    module = _remote_agent_protocol_example()

    monkeypatch.setenv("BUB_AGENT_PROTOCOL_URL", "http://remote")
    monkeypatch.setenv("BUB_AGENT_PROTOCOL_AGENT_ID", "agent")

    request = LangchainFactoryRequest(
        state={},
        session_id="session-1",
        workspace=tmp_path,
        tools=[],
        system_prompt="system",
        prompt=[{"type": "text", "text": "hello remote"}],
        langchain_context=_run_context(),
    )

    binding = module.remote_agent_protocol_agent(request=request)

    assert binding.invoke_input == request.prompt
    assert isinstance(binding.runnable, AgentProtocolRunnable)
    assert binding.output_parser is module._parse_remote_agent_output


def test_remote_output_parser_extracts_visible_text_blocks() -> None:
    module = _remote_agent_protocol_example()

    payload = '[{"signature":"","thinking":"internal","type":"thinking"},{"text":"Visible answer","type":"text"}]'

    assert module._parse_remote_agent_output(payload) == "Visible answer"
