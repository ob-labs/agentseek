from __future__ import annotations

from collections.abc import Awaitable, Callable
from functools import wraps
from typing import Any

import logfire
from republic import AsyncStreamEvents, AsyncTextStream, StreamEvents, TextStream

from agentseek_observability._patches import (
    PatchRegistry,
    close_span,
    safe_count,
    wrap_async_iterator_with_span,
    wrap_iterator_with_span,
)


def _wrap_republic_result(result: Any, span_cm: Any) -> Any:
    if isinstance(result, TextStream):
        return TextStream(wrap_iterator_with_span(iter(result), span_cm), state=result._state)
    if isinstance(result, AsyncTextStream):
        return AsyncTextStream(wrap_async_iterator_with_span(result.__aiter__(), span_cm), state=result._state)
    if isinstance(result, StreamEvents):
        return StreamEvents(wrap_iterator_with_span(iter(result), span_cm), state=result._state)
    if isinstance(result, AsyncStreamEvents):
        return AsyncStreamEvents(wrap_async_iterator_with_span(result.__aiter__(), span_cm), state=result._state)
    return result


def _tool_name(tool_response: Any) -> str:
    if isinstance(tool_response, dict):
        function = tool_response.get("function")
        if isinstance(function, dict):
            return str(function.get("name", "unknown"))
    return "unknown"


def _run_sync_call_with_optional_stream(
    call: Callable[[], Any],
    span_cm: Any,
    *,
    stream: bool,
) -> Any:
    span_cm.__enter__()
    error: BaseException | None = None
    result: Any | None = None
    is_stream_result = False
    try:
        result = call()
    except BaseException as exc:
        error = exc
        raise
    else:
        is_stream_result = stream
        if is_stream_result:
            return _wrap_republic_result(result, span_cm)
        return result
    finally:
        if error is not None or not is_stream_result:
            close_span(span_cm, error)


async def _run_async_call_with_optional_stream(
    call: Callable[[], Awaitable[Any]],
    span_cm: Any,
    *,
    stream: bool,
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
        is_stream_result = stream
        if is_stream_result:
            return _wrap_republic_result(result, span_cm)
        return result
    finally:
        if error is not None or not is_stream_result:
            close_span(span_cm, error)


def _wrap_run_chat_sync(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
            provider = kwargs.get("provider") or self.provider
            model = kwargs.get("model") or self.model
            stream = bool(kwargs.get("stream"))
            span_cm = layer.span(
                "Run republic chat {provider}:{model}",
                provider=provider,
                model=model,
                stream=stream,
                message_count=safe_count(kwargs.get("messages_payload")),
                tool_count=safe_count(kwargs.get("tools_payload")),
                max_attempts=self.max_attempts(),
                fallback_models=safe_count(self.fallback_models),
                _span_name="republic.run_chat",
            )
            return _run_sync_call_with_optional_stream(
                lambda: original(self, *args, **kwargs),
                span_cm,
                stream=stream,
            )

        return wrapped

    return wrapper_factory


def _wrap_run_chat_async(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
            provider = kwargs.get("provider") or self.provider
            model = kwargs.get("model") or self.model
            stream = bool(kwargs.get("stream"))
            span_cm = layer.span(
                "Run republic chat {provider}:{model}",
                provider=provider,
                model=model,
                stream=stream,
                message_count=safe_count(kwargs.get("messages_payload")),
                tool_count=safe_count(kwargs.get("tools_payload")),
                max_attempts=self.max_attempts(),
                fallback_models=safe_count(self.fallback_models),
                _span_name="republic.run_chat",
            )
            return await _run_async_call_with_optional_stream(
                lambda: original(self, *args, **kwargs),
                span_cm,
                stream=stream,
            )

        return wrapped

    return wrapper_factory


def _wrap_execute_sync(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(self: Any, response: Any, tools: Any = None, *, context: Any = None) -> Any:
            span_cm = layer.span(
                "Execute republic tools",
                tool_call_count=safe_count(response),
                tape=getattr(context, "tape", None),
                run_id=getattr(context, "run_id", None),
                _span_name="republic.execute_tools",
            )
            with span_cm:
                return original(self, response, tools, context=context)

        return wrapped

    return wrapper_factory


def _wrap_execute_async(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(self: Any, response: Any, tools: Any = None, *, context: Any = None) -> Any:
            span_cm = layer.span(
                "Execute republic tools",
                tool_call_count=safe_count(response),
                tape=getattr(context, "tape", None),
                run_id=getattr(context, "run_id", None),
                _span_name="republic.execute_tools",
            )
            with span_cm:
                return await original(self, response, tools, context=context)

        return wrapped

    return wrapper_factory


def _wrap_handle_tool_response_sync(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(self: Any, tool_response: Any, tool_map: Any, context: Any) -> Any:
            span_cm = layer.span(
                "Run republic tool {tool_name}",
                tool_name=_tool_name(tool_response),
                tape=getattr(context, "tape", None),
                run_id=getattr(context, "run_id", None),
                _span_name="republic.tool_call",
            )
            with span_cm:
                return original(self, tool_response, tool_map, context)

        return wrapped

    return wrapper_factory


def _wrap_handle_tool_response_async(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(self: Any, tool_response: Any, tool_map: Any, context: Any) -> Any:
            span_cm = layer.span(
                "Run republic tool {tool_name}",
                tool_name=_tool_name(tool_response),
                tape=getattr(context, "tape", None),
                run_id=getattr(context, "run_id", None),
                _span_name="republic.tool_call",
            )
            with span_cm:
                return await original(self, tool_response, tool_map, context)

        return wrapped

    return wrapper_factory


def _record_chat_kwargs(kwargs: dict[str, Any]) -> dict[str, Any]:
    return {
        "tape": kwargs.get("tape"),
        "run_id": kwargs.get("run_id"),
        "provider": kwargs.get("provider"),
        "model": kwargs.get("model"),
        "status": "error" if kwargs.get("error") is not None else "ok",
        "new_messages": safe_count(kwargs.get("new_messages")),
        "tool_calls": safe_count(kwargs.get("tool_calls")),
        "tool_results": safe_count(kwargs.get("tool_results")),
        "_span_name": "republic.record_chat",
    }


def _wrap_record_chat_sync(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
            span_cm = layer.span("Record republic chat {tape}", **_record_chat_kwargs(kwargs))
            with span_cm:
                return original(self, *args, **kwargs)

        return wrapped

    return wrapper_factory


def _wrap_record_chat_async(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(self: Any, *args: Any, **kwargs: Any) -> Any:
            span_cm = layer.span("Record republic chat {tape}", **_record_chat_kwargs(kwargs))
            with span_cm:
                return await original(self, *args, **kwargs)

        return wrapped

    return wrapper_factory


def instrument_republic(
    logfire_instance: logfire.Logfire,
    registry: PatchRegistry,
) -> None:
    from republic.core.execution import LLMCore
    from republic.tape.manager import AsyncTapeManager, TapeManager
    from republic.tools.executor import ToolExecutor

    layer = logfire_instance.with_settings(custom_scope_suffix="republic", tags=["agentseek", "republic"])
    registry.patch(LLMCore, "run_chat_sync", _wrap_run_chat_sync(layer))
    registry.patch(LLMCore, "run_chat_async", _wrap_run_chat_async(layer))
    registry.patch(ToolExecutor, "execute", _wrap_execute_sync(layer))
    registry.patch(ToolExecutor, "execute_async", _wrap_execute_async(layer))
    registry.patch(ToolExecutor, "_handle_tool_response", _wrap_handle_tool_response_sync(layer))
    registry.patch(ToolExecutor, "_handle_tool_response_async", _wrap_handle_tool_response_async(layer))
    registry.patch(TapeManager, "record_chat", _wrap_record_chat_sync(layer))
    registry.patch(AsyncTapeManager, "record_chat", _wrap_record_chat_async(layer))
