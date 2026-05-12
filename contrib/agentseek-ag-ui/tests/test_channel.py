from __future__ import annotations

import asyncio
from typing import Any

from ag_ui.core import Context, RunAgentInput, TextInputContent, Tool, UserMessage
from ag_ui.encoder import EventEncoder
from agentseek_ag_ui.channel import AGUIChannel
from agentseek_ag_ui.config import AGUISettings
from agentseek_ag_ui.plugin import AGUIPlugin
from bub.channels.message import ChannelMessage
from republic import StreamEvent


def _input(*, state: Any = None) -> RunAgentInput:
    return RunAgentInput(
        thread_id="thread-1",
        run_id="run-1",
        parent_run_id=None,
        state={} if state is None else state,
        messages=[
            UserMessage(
                id="user-1",
                content=[
                    TextInputContent(text="describe the image"),
                ],
            )
        ],
        tools=[Tool(name="lookup", description="Lookup data")],
        context=[Context(description="tenant", value="demo")],
        forwarded_props={},
    )


def _decode_payloads(chunks: list[str]) -> list[str]:
    payloads: list[str] = []
    for chunk in chunks:
        for line in chunk.splitlines():
            if line.startswith("data: "):
                payloads.append(line[len("data: ") :])
    return payloads


async def _drain_queue(active: Any) -> list[str]:
    chunks: list[str] = []
    while not active.queue.empty():
        item = await active.queue.get()
        if item is not None:
            chunks.append(item)
    return chunks


def test_channel_wraps_parent_stream_and_preserves_original_events() -> None:
    channel = AGUIChannel(lambda message: None, settings=AGUISettings(host="127.0.0.1", port=18088))
    input_data = _input(state={"count": 1})
    message = channel.build_message(input_data)
    active = asyncio.run(channel.register_request(input_data, encoder=EventEncoder("")))

    async def iterator():
        yield StreamEvent("text", {"delta": "Hello"})
        yield StreamEvent(
            "tool_call",
            {
                "index": 0,
                "call": {
                    "id": "call-1",
                    "type": "function",
                    "function": {"name": "lookup", "arguments": '{"city":"Shanghai"}'},
                },
            },
        )
        yield StreamEvent("tool_result", {"index": 0, "result": {"weather": "sunny"}})
        yield StreamEvent("usage", {"input_tokens": 10, "output_tokens": 5})

    forwarded = asyncio.run(_collect_stream(channel, message, iterator()))

    assert [event.kind for event in forwarded] == ["text", "tool_call", "tool_result", "usage"]

    chunks = asyncio.run(_drain_queue(active))
    payloads = _decode_payloads(chunks)
    assert any('"type":"RUN_STARTED"' in payload for payload in payloads)
    assert any('"type":"STATE_SNAPSHOT"' in payload and '"count":1' in payload for payload in payloads)
    assert any('"type":"TEXT_MESSAGE_CONTENT"' in payload and '"delta":"Hello"' in payload for payload in payloads)
    assert any('"type":"TOOL_CALL_RESULT"' in payload for payload in payloads)
    assert any('"name":"republic.usage"' in payload for payload in payloads)


def test_plugin_build_prompt_and_save_state() -> None:
    plugin = AGUIPlugin(framework=None)
    input_data = _input(state={"count": 1})
    message = plugin._channel.build_message(input_data)
    active = asyncio.run(plugin._channel.register_request(input_data, encoder=EventEncoder("")))

    prompt = asyncio.run(plugin.build_prompt(message=message, session_id="thread-1", state={}))
    assert prompt == "tenant: demo\ndescribe the image"
    assert plugin.load_state(message, "thread-1") == {"ag_ui": {"count": 1}}

    asyncio.run(
        plugin.save_state(
            session_id="thread-1",
            state={"count": 2, "session_id": "thread-1"},
            message=message,
            model_output="Done",
        )
    )
    staged_payloads = _decode_payloads(asyncio.run(_drain_queue(active)))
    assert any('"type":"RUN_STARTED"' in payload for payload in staged_payloads)
    assert any('"type":"STATE_SNAPSHOT"' in payload and '"count":1' in payload for payload in staged_payloads)
    assert not any('"type":"TEXT_MESSAGE_CONTENT"' in payload for payload in staged_payloads)
    assert not any('"type":"RUN_FINISHED"' in payload for payload in staged_payloads)

    outbound = ChannelMessage(
        session_id="thread-1",
        channel="ag-ui",
        chat_id="thread-1",
        content="Done",
    )
    asyncio.run(plugin._channel.send(outbound))

    chunks = asyncio.run(_drain_queue(active))
    payloads = _decode_payloads(chunks)
    assert any('"type":"TEXT_MESSAGE_CONTENT"' in payload and '"delta":"Done"' in payload for payload in payloads)
    assert any('"type":"STATE_SNAPSHOT"' in payload and '"count":2' in payload for payload in payloads)
    assert any('"type":"TEXT_MESSAGE_END"' in payload for payload in payloads)
    assert any('"type":"RUN_FINISHED"' in payload for payload in payloads)
    assert sum('"type":"TEXT_MESSAGE_CONTENT"' in payload for payload in payloads) == 1


def test_plugin_on_error_emits_run_error_instead_of_run_finished() -> None:
    plugin = AGUIPlugin(framework=None)
    input_data = _input(state={"count": 1})
    message = plugin._channel.build_message(input_data)
    active = asyncio.run(plugin._channel.register_request(input_data, encoder=EventEncoder("")))

    asyncio.run(
        plugin.save_state(
            session_id="thread-1",
            state={"count": 2},
            message=message,
            model_output="partial output",
        )
    )
    asyncio.run(plugin.on_error("turn", RuntimeError("boom"), message))

    payloads = _decode_payloads(asyncio.run(_drain_queue(active)))
    assert any('"type":"RUN_ERROR"' in payload and '"message":"boom"' in payload for payload in payloads)
    assert not any('"type":"RUN_FINISHED"' in payload for payload in payloads)


def test_channel_send_fallback_emits_terminal_events() -> None:
    channel = AGUIChannel(lambda message: None, settings=AGUISettings(host="127.0.0.1", port=18089))
    input_data = _input()
    active = asyncio.run(channel.register_request(input_data, encoder=EventEncoder("")))

    outbound = ChannelMessage(
        session_id="thread-1",
        channel="ag-ui",
        chat_id="thread-1",
        content="fallback output",
    )
    asyncio.run(channel.send(outbound))

    chunks = asyncio.run(_drain_queue(active))
    payloads = _decode_payloads(chunks)
    assert any(
        '"type":"TEXT_MESSAGE_CONTENT"' in payload and '"delta":"fallback output"' in payload for payload in payloads
    )
    assert any('"type":"RUN_FINISHED"' in payload for payload in payloads)


def test_channel_stream_error_event_emits_run_error_and_closes_request() -> None:
    channel = AGUIChannel(lambda message: None, settings=AGUISettings(host="127.0.0.1", port=18090))
    input_data = _input()
    message = channel.build_message(input_data)
    active = asyncio.run(channel.register_request(input_data, encoder=EventEncoder("")))

    async def iterator():
        yield StreamEvent("text", {"delta": "partial"})
        yield StreamEvent("error", {"message": "stream failed", "kind": "runtime_error"})

    forwarded = asyncio.run(_collect_stream(channel, message, iterator()))

    assert [event.kind for event in forwarded] == ["text", "error"]

    payloads = _decode_payloads(asyncio.run(_drain_queue(active)))
    assert any('"type":"TEXT_MESSAGE_CONTENT"' in payload and '"delta":"partial"' in payload for payload in payloads)
    assert any('"type":"TEXT_MESSAGE_END"' in payload for payload in payloads)
    assert any('"type":"RUN_ERROR"' in payload and '"message":"stream failed"' in payload for payload in payloads)
    assert not any('"type":"RUN_FINISHED"' in payload for payload in payloads)
    assert active.finished is True


async def _collect_stream(channel: AGUIChannel, message: ChannelMessage, iterator: Any) -> list[StreamEvent]:
    return [event async for event in channel.stream_events(message, iterator)]
