from __future__ import annotations

import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator, AsyncIterable
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import uvicorn
from ag_ui.core import (
    CustomEvent,
    EventType,
    RunAgentInput,
    RunErrorEvent,
    RunFinishedEvent,
    RunStartedEvent,
    StateSnapshotEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
    TextMessageStartEvent,
    ToolCallArgsEvent,
    ToolCallEndEvent,
    ToolCallResultEvent,
    ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder
from bub.channels.base import Channel
from bub.channels.message import ChannelMessage, MediaItem
from bub.envelope import content_of
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from republic import StreamEvent

from agentseek_ag_ui.config import AGUISettings

_INPUT_ATTR = "_agentseek_ag_ui_input"
_RUN_ID_ATTR = "_agentseek_ag_ui_run_id"
_PRIMITIVE_TYPES = (str, int, float, bool, type(None))


@dataclass
class _ActiveRequest:
    input_data: RunAgentInput
    encoder: EventEncoder
    queue: asyncio.Queue[str | None] = field(default_factory=asyncio.Queue)
    assistant_message_id: str = field(default_factory=lambda: f"assistant-{uuid4().hex}")
    run_started_emitted: bool = False
    initial_snapshot_emitted: bool = False
    assistant_started: bool = False
    assistant_ended: bool = False
    failed: bool = False
    finished: bool = False
    final_text_parts: list[str] = field(default_factory=list)
    tool_call_ids: dict[int, str] = field(default_factory=dict)
    initial_snapshot: dict[str, Any] = field(default_factory=dict)
    pending_snapshot: dict[str, Any] = field(default_factory=dict)
    pending_model_output: str | None = None

    async def emit(self, event: Any) -> None:
        if self.finished:
            return
        await self.queue.put(self.encoder.encode(event))

    async def close(self) -> None:
        if self.finished:
            return
        self.finished = True
        await self.queue.put(None)


class AGUIChannel(Channel):
    name = "ag-ui"

    def __init__(self, on_receive: Any, *, settings: AGUISettings | None = None) -> None:
        self._on_receive = on_receive
        self.settings = settings or AGUISettings()
        self._server: uvicorn.Server | None = None
        self._server_task: asyncio.Task[None] | None = None
        self._active_by_run_id: dict[str, _ActiveRequest] = {}
        self._active_runs_by_session: dict[str, set[str]] = {}
        self._lock = asyncio.Lock()
        self.app = self._build_app()

    def bind_receiver(self, on_receive: Any) -> None:
        self._on_receive = on_receive

    async def start(self, stop_event: asyncio.Event) -> None:
        del stop_event
        if self._server_task is not None and not self._server_task.done():
            return
        config = uvicorn.Config(
            self.app,
            host=self.settings.host,
            port=self.settings.port,
            loop="asyncio",
            log_level="info",
        )
        self._server = uvicorn.Server(config)
        self._server_task = asyncio.create_task(self._server.serve(), name="agentseek-ag-ui.server")
        await self._wait_until_started()

    async def stop(self) -> None:
        server = self._server
        task = self._server_task
        self._server = None
        self._server_task = None
        if server is not None:
            server.should_exit = True
        if task is not None and not task.done():
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await self._close_all_requests()

    async def send(self, message: ChannelMessage) -> None:
        active = await self._lookup_request(message)
        if active is None or active.finished:
            return
        content = content_of(message)
        await self._emit_run_started(active)
        await self._emit_initial_snapshot(active)
        if message.kind == "error":
            await self.publish_error(message, error=content or "dispatch error", code="dispatch_error")
            return

        snapshot = active.pending_snapshot
        if snapshot and snapshot != active.initial_snapshot:
            await active.emit(StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=snapshot))
        active.pending_snapshot = {}

        if content and not active.assistant_started:
            await self._emit_text_delta(active, delta=content)
        elif not content and active.pending_model_output and not active.assistant_started:
            await self._emit_text_delta(active, delta=active.pending_model_output)
        active.pending_model_output = None

        await self._emit_text_end(active)
        await active.emit(
            RunFinishedEvent(
                type=EventType.RUN_FINISHED,
                thread_id=active.input_data.thread_id,
                run_id=active.input_data.run_id,
                result={"text": "".join(active.final_text_parts)} if active.final_text_parts else None,
            )
        )
        await active.close()
        await self._remove_request(active.input_data.thread_id, active.input_data.run_id)

    async def publish_error(self, message: ChannelMessage, *, error: str, code: str) -> None:
        active = await self._lookup_request(message)
        if active is None or active.finished:
            return
        active.failed = True
        await self._emit_run_started(active)
        await self._emit_initial_snapshot(active)
        if active.pending_snapshot and active.pending_snapshot != active.initial_snapshot:
            await active.emit(StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=active.pending_snapshot))
        await self._emit_text_end(active)
        await active.emit(
            RunErrorEvent(
                type=EventType.RUN_ERROR,
                message=error,
                code=code,
            )
        )
        active.pending_snapshot = {}
        active.pending_model_output = None
        await active.close()
        await self._remove_request(active.input_data.thread_id, active.input_data.run_id)

    def stream_events(self, message: ChannelMessage, stream: AsyncIterable[StreamEvent]) -> AsyncIterable[StreamEvent]:
        return self._stream_events(message, stream)

    async def publish_state(self, message: ChannelMessage, state: dict[str, Any]) -> None:
        await self.publish_result(message, state=state, model_output=None)

    async def publish_result(
        self,
        message: ChannelMessage,
        *,
        state: dict[str, Any],
        model_output: str | None,
    ) -> None:
        active = await self._lookup_request(message)
        if active is None or active.finished:
            return
        await self._emit_run_started(active)
        await self._emit_initial_snapshot(active)
        snapshot = _public_state_snapshot(state)
        active.pending_snapshot = snapshot
        active.pending_model_output = model_output

    def build_message(self, input_data: RunAgentInput) -> ChannelMessage:
        content, media = _select_message_payload(input_data.messages)
        message = ChannelMessage(
            session_id=input_data.thread_id,
            channel=self.name,
            chat_id=input_data.thread_id,
            content=content,
            context={},
            media=media,
        )
        setattr(message, _INPUT_ATTR, input_data)
        setattr(message, _RUN_ID_ATTR, input_data.run_id)
        return message

    async def register_request(self, input_data: RunAgentInput, *, encoder: EventEncoder) -> _ActiveRequest:
        active = _ActiveRequest(
            input_data=input_data,
            encoder=encoder,
            initial_snapshot=_public_state_snapshot(input_data.state),
        )
        async with self._lock:
            self._active_by_run_id[input_data.run_id] = active
            self._active_runs_by_session.setdefault(input_data.thread_id, set()).add(input_data.run_id)
        return active

    def input_for(self, message: ChannelMessage) -> RunAgentInput | None:
        input_data = getattr(message, _INPUT_ATTR, None)
        return input_data if isinstance(input_data, RunAgentInput) else None

    async def _stream_events(
        self, message: ChannelMessage, stream: AsyncIterable[StreamEvent]
    ) -> AsyncGenerator[StreamEvent, None]:
        active = await self._lookup_request(message)
        if active is None:
            async for event in stream:
                yield event
            return
        await self._emit_run_started(active)
        await self._emit_initial_snapshot(active)
        async for event in stream:
            await self._emit_stream_side_effect(active, event)
            yield event

    async def _emit_stream_side_effect(self, active: _ActiveRequest, event: StreamEvent) -> None:
        if active.finished:
            return
        if event.kind == "text":
            await self._emit_text_delta(active, delta=_to_text(event.data.get("delta")))
            return
        if event.kind == "tool_call":
            call = event.data.get("call") or {}
            index = int(event.data.get("index", len(active.tool_call_ids)))
            tool_call_id = _tool_call_id(call, fallback_prefix=active.input_data.run_id, index=index)
            active.tool_call_ids[index] = tool_call_id
            await active.emit(
                ToolCallStartEvent(
                    type=EventType.TOOL_CALL_START,
                    tool_call_id=tool_call_id,
                    tool_call_name=_tool_call_name(call),
                    parent_message_id=active.assistant_message_id if active.assistant_started else None,
                )
            )
            arguments = _tool_call_arguments(call)
            if arguments:
                await active.emit(
                    ToolCallArgsEvent(
                        type=EventType.TOOL_CALL_ARGS,
                        tool_call_id=tool_call_id,
                        delta=arguments,
                    )
                )
            await active.emit(ToolCallEndEvent(type=EventType.TOOL_CALL_END, tool_call_id=tool_call_id))
            return
        if event.kind == "tool_result":
            index = int(event.data.get("index", 0))
            tool_call_id = active.tool_call_ids.get(index, f"{active.input_data.run_id}-tool-{index}")
            await active.emit(
                ToolCallResultEvent(
                    type=EventType.TOOL_CALL_RESULT,
                    message_id=f"{tool_call_id}-result",
                    tool_call_id=tool_call_id,
                    content=_json_text(event.data.get("result")),
                    role="tool",
                )
            )
            return
        if event.kind == "usage":
            await active.emit(
                CustomEvent(
                    type=EventType.CUSTOM,
                    name="republic.usage",
                    value=_to_record(event.data),
                )
            )
            return
        if event.kind == "error":
            active.failed = True
            await self._emit_text_end(active)
            await active.emit(
                RunErrorEvent(
                    type=EventType.RUN_ERROR,
                    message=str(event.data.get("message", "unknown error")),
                    code=str(event.data.get("kind", "runtime_error")),
                )
            )
            await active.close()
            await self._remove_request(active.input_data.thread_id, active.input_data.run_id)

    async def _emit_text_delta(self, active: _ActiveRequest, *, delta: str) -> None:
        if not delta:
            return
        if not active.assistant_started:
            await active.emit(
                TextMessageStartEvent(
                    type=EventType.TEXT_MESSAGE_START,
                    message_id=active.assistant_message_id,
                    role="assistant",
                )
            )
            active.assistant_started = True
        active.final_text_parts.append(delta)
        await active.emit(
            TextMessageContentEvent(
                type=EventType.TEXT_MESSAGE_CONTENT,
                message_id=active.assistant_message_id,
                delta=delta,
            )
        )

    async def _emit_text_end(self, active: _ActiveRequest) -> None:
        if not active.assistant_started or active.assistant_ended:
            return
        await active.emit(
            TextMessageEndEvent(
                type=EventType.TEXT_MESSAGE_END,
                message_id=active.assistant_message_id,
            )
        )
        active.assistant_ended = True

    async def _emit_run_started(self, active: _ActiveRequest) -> None:
        if active.run_started_emitted:
            return
        await active.emit(_run_started_event(active))
        active.run_started_emitted = True

    async def _emit_initial_snapshot(self, active: _ActiveRequest) -> None:
        if active.initial_snapshot_emitted or not active.initial_snapshot:
            return
        await active.emit(StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=active.initial_snapshot))
        active.initial_snapshot_emitted = True

    async def _lookup_request(self, message: ChannelMessage) -> _ActiveRequest | None:
        run_id = getattr(message, _RUN_ID_ATTR, None)
        async with self._lock:
            if isinstance(run_id, str) and run_id in self._active_by_run_id:
                return self._active_by_run_id[run_id]
            run_ids = self._active_runs_by_session.get(message.session_id, set())
            if len(run_ids) == 1:
                only_run_id = next(iter(run_ids))
                return self._active_by_run_id.get(only_run_id)
        return None

    async def _remove_request(self, session_id: str, run_id: str) -> None:
        async with self._lock:
            self._active_by_run_id.pop(run_id, None)
            run_ids = self._active_runs_by_session.get(session_id)
            if run_ids is None:
                return
            run_ids.discard(run_id)
            if not run_ids:
                self._active_runs_by_session.pop(session_id, None)

    async def _close_all_requests(self) -> None:
        async with self._lock:
            active_requests = list(self._active_by_run_id.values())
            self._active_by_run_id.clear()
            self._active_runs_by_session.clear()
        for active in active_requests:
            await active.close()

    async def _wait_until_started(self) -> None:
        server = self._server
        task = self._server_task
        if server is None or task is None:
            return
        while not server.started and not task.done():
            await asyncio.sleep(0.01)

    def _build_app(self) -> FastAPI:
        app = FastAPI(title="agentseek AG-UI channel")

        @app.post(self.settings.path)
        async def ag_ui_endpoint(input_data: RunAgentInput, request: Request):
            encoder = EventEncoder(accept=request.headers.get("accept") or "")
            active = await self.register_request(input_data, encoder=encoder)
            message = self.build_message(input_data)
            try:
                await self._on_receive(message)
            except Exception as exc:
                await self.publish_error(
                    message,
                    error=str(exc) or exc.__class__.__name__,
                    code=type(exc).__name__,
                )

            async def event_generator() -> AsyncGenerator[str, None]:
                try:
                    while True:
                        item = await active.queue.get()
                        if item is None:
                            break
                        yield item
                finally:
                    await self._remove_request(input_data.thread_id, input_data.run_id)

            return StreamingResponse(event_generator(), media_type=encoder.get_content_type())

        @app.get(self.settings.health_path)
        def health() -> dict[str, Any]:
            return {
                "status": "ok",
                "channel": self.name,
                "host": self.settings.host,
                "port": self.settings.port,
                "path": self.settings.path,
            }

        return app


def _run_started_event(active: _ActiveRequest) -> RunStartedEvent:
    return RunStartedEvent(
        type=EventType.RUN_STARTED,
        thread_id=active.input_data.thread_id,
        run_id=active.input_data.run_id,
        parent_run_id=active.input_data.parent_run_id,
        input=active.input_data,
    )


def _select_message_payload(messages: list[Any]) -> tuple[str, list[MediaItem]]:
    user_messages = [message for message in messages if getattr(message, "role", None) == "user"]
    source = user_messages[-1] if user_messages else (messages[-1] if messages else None)
    if source is None:
        return "", []
    content = getattr(source, "content", "")
    if isinstance(content, str):
        return content, []
    if isinstance(content, list):
        text_parts: list[str] = []
        media: list[MediaItem] = []
        for part in content:
            part_type = getattr(part, "type", None)
            if part_type == "text":
                text = getattr(part, "text", "")
                if text:
                    text_parts.append(str(text))
                continue
            media_item = _to_media_item(part)
            if media_item is not None:
                media.append(media_item)
        return "\n".join(text_parts).strip(), media
    return _to_text(content), []


def _to_media_item(part: Any) -> MediaItem | None:
    part_type = getattr(part, "type", None)
    if part_type not in {"image", "audio", "video", "document"}:
        return None
    source = getattr(part, "source", None)
    source_type = getattr(source, "type", None)
    mime_type = getattr(source, "mime_type", None) or "application/octet-stream"
    url: str | None = None
    if source_type == "url":
        url = getattr(source, "value", None)
    elif source_type == "data":
        value = getattr(source, "value", None)
        if value:
            url = f"data:{mime_type};base64,{value}"
    if not url:
        return None
    return MediaItem(type=part_type, mime_type=mime_type, url=url)


def _tool_call_id(call: Any, *, fallback_prefix: str, index: int) -> str:
    if isinstance(call, dict):
        call_id = call.get("id")
        if call_id:
            return str(call_id)
    return f"{fallback_prefix}-tool-{index}"


def _tool_call_name(call: Any) -> str:
    if isinstance(call, dict):
        function = call.get("function")
        if isinstance(function, dict) and function.get("name"):
            return str(function["name"])
        if call.get("name"):
            return str(call["name"])
    return "tool"


def _tool_call_arguments(call: Any) -> str:
    if not isinstance(call, dict):
        return ""
    function = call.get("function")
    if isinstance(function, dict):
        arguments = function.get("arguments")
        if isinstance(arguments, str):
            return arguments
        if arguments is not None:
            return _json_text(arguments)
    arguments = call.get("arguments")
    if isinstance(arguments, str):
        return arguments
    if arguments is not None:
        return _json_text(arguments)
    return ""


def _public_state_snapshot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): _to_record(item)
        for key, item in value.items()
        if not str(key).startswith("_") and str(key) != "session_id"
    }


def _to_record(value: Any) -> Any:
    if isinstance(value, _PRIMITIVE_TYPES):
        return value
    if isinstance(value, dict):
        return {str(key): _to_record(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_to_record(item) for item in value]
    if hasattr(value, "model_dump"):
        return _to_record(value.model_dump())
    if hasattr(value, "content"):
        return _to_record(value.content)
    return str(value)


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(part for part in (_to_text(item) for item in value) if part)
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"]
        if "content" in value:
            return _to_text(value["content"])
        return _json_text(value)
    if hasattr(value, "content"):
        return _to_text(value.content)
    return str(value)


def _json_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(_to_record(value), ensure_ascii=False, default=str)
