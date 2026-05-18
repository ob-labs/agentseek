from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any, cast

import logfire
from republic import AsyncStreamEvents

from agentseek_observability._patches import PatchRegistry, close_span, safe_count, wrap_async_iterator_with_span


def _field(message: object, key: str, default: object = None) -> object:
    if isinstance(message, dict):
        message_mapping = cast("dict[str, Any]", message)
        return message_mapping.get(key, default)
    return getattr(message, key, default)


def _prompt_type(prompt: object) -> str:
    return "messages" if isinstance(prompt, list) else "text"


def _wrap_stream_events_result(result: Any, span_cm: Any) -> Any:
    if isinstance(result, AsyncStreamEvents):
        return AsyncStreamEvents(wrap_async_iterator_with_span(result.__aiter__(), span_cm), state=result._state)
    return result


async def _run_async_call_with_optional_stream_events(
    call: Callable[[], Awaitable[Any]],
    span_cm: Any,
    *,
    stream_output: bool,
) -> Any:
    span_cm.__enter__()
    error: BaseException | None = None
    result: Any | None = None
    is_stream_result = False
    try:
        result = await call()
    except BaseException as exc:
        error = exc
        raise
    else:
        is_stream_result = stream_output and isinstance(result, AsyncStreamEvents)
        if is_stream_result:
            return _wrap_stream_events_result(result, span_cm)
        return result
    finally:
        if error is not None or not is_stream_result:
            close_span(span_cm, error)


def _wrap_process_inbound(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(self: Any, inbound: object, stream_output: bool = False) -> Any:
            span_cm = layer.span(
                "Process bub inbound {channel}",
                channel=_field(inbound, "channel", "default"),
                chat_id=_field(inbound, "chat_id", "default"),
                session_id=_field(inbound, "session_id"),
                stream_output=stream_output,
                kind=_field(inbound, "kind", "normal"),
                _span_name="bub.process_inbound",
            )
            with span_cm:
                return await original(self, inbound, stream_output=stream_output)

        return wrapped

    return wrapper_factory


def _wrap_run(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(
            self: Any,
            *,
            session_id: str,
            prompt: object,
            state: object,
            model: str | None = None,
            allowed_skills: object = None,
            allowed_tools: object = None,
        ) -> Any:
            span_cm = layer.span(
                "Run bub agent {session_id}",
                session_id=session_id,
                prompt_type=_prompt_type(prompt),
                model=model or self.settings.model,
                allowed_skills=safe_count(allowed_skills),
                allowed_tools=safe_count(allowed_tools),
                _span_name="bub.agent.run",
            )
            with span_cm:
                return await original(
                    self,
                    session_id=session_id,
                    prompt=prompt,
                    state=state,
                    model=model,
                    allowed_skills=allowed_skills,
                    allowed_tools=allowed_tools,
                )

        return wrapped

    return wrapper_factory


def _wrap_run_stream(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(
            self: Any,
            *,
            session_id: str,
            prompt: object,
            state: object,
            model: str | None = None,
            allowed_skills: object = None,
            allowed_tools: object = None,
        ) -> Any:
            span_cm = layer.span(
                "Run bub agent stream {session_id}",
                session_id=session_id,
                prompt_type=_prompt_type(prompt),
                model=model or self.settings.model,
                allowed_skills=safe_count(allowed_skills),
                allowed_tools=safe_count(allowed_tools),
                _span_name="bub.agent.run_stream",
            )
            return await _run_async_call_with_optional_stream_events(
                lambda: original(
                    self,
                    session_id=session_id,
                    prompt=prompt,
                    state=state,
                    model=model,
                    allowed_skills=allowed_skills,
                    allowed_tools=allowed_tools,
                ),
                span_cm,
                stream_output=True,
            )

        return wrapped

    return wrapper_factory


def _wrap_run_once(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(
            self: Any,
            *,
            tape: Any,
            prompt: object,
            model: str | None = None,
            allowed_tools: object = None,
            allowed_skills: object = None,
            stream_output: bool = False,
        ) -> Any:
            span_cm = layer.span(
                "Run bub step {tape}",
                tape=tape.name,
                prompt_type=_prompt_type(prompt),
                model=model or self.settings.model,
                stream_output=stream_output,
                allowed_skills=safe_count(allowed_skills),
                allowed_tools=safe_count(allowed_tools),
                _span_name="bub.agent.step",
            )
            return await _run_async_call_with_optional_stream_events(
                lambda: original(
                    self,
                    tape=tape,
                    prompt=prompt,
                    model=model,
                    allowed_tools=allowed_tools,
                    allowed_skills=allowed_skills,
                    stream_output=stream_output,
                ),
                span_cm,
                stream_output=stream_output,
            )

        return wrapped

    return wrapper_factory


def instrument_bub(
    logfire_instance: logfire.Logfire,
    registry: PatchRegistry,
) -> None:
    from bub.builtin.agent import Agent
    from bub.framework import BubFramework

    layer = logfire_instance.with_settings(custom_scope_suffix="bub", tags=["agentseek", "bub"])
    registry.patch(BubFramework, "process_inbound", _wrap_process_inbound(layer))
    registry.patch(Agent, "run", _wrap_run(layer))
    registry.patch(Agent, "run_stream", _wrap_run_stream(layer))
    registry.patch(Agent, "_run_once", _wrap_run_once(layer))
