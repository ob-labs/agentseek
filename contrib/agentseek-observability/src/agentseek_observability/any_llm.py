from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable
from functools import wraps
from typing import Any

import logfire

from agentseek_observability._patches import PatchRegistry, close_span, safe_count, wrap_async_iterator_with_span


def _provider_name(value: object) -> str:
    return str(getattr(value, "value", value))


def _input_items(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return 1
    return safe_count(value)


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
        is_stream_result = stream and isinstance(result, AsyncIterator)
        if is_stream_result:
            return wrap_async_iterator_with_span(result, span_cm)
        return result
    finally:
        if error is not None or not is_stream_result:
            close_span(span_cm, error)


def _wrap_create(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        def wrapped(cls: type[Any], provider: object, *args: Any, **kwargs: Any) -> Any:
            span_cm = layer.span(
                "Create any-llm provider {provider}",
                provider=_provider_name(provider),
                has_api_base=bool(kwargs.get("api_base")),
                _span_name="any_llm.create",
            )
            with span_cm:
                return original(cls, provider, *args, **kwargs)

        return wrapped

    return wrapper_factory


def _wrap_acompletion(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(self: Any, model: str, messages: object, *args: Any, **kwargs: Any) -> Any:
            stream = bool(kwargs.get("stream"))
            span_cm = layer.span(
                "Run any-llm completion {provider}:{model}",
                provider=self.PROVIDER_NAME,
                model=model,
                stream=stream,
                message_count=safe_count(messages),
                tool_count=safe_count(kwargs.get("tools")),
                _span_name="any_llm.completion",
            )
            return await _run_async_call_with_optional_stream(
                lambda: original(self, model, messages, *args, **kwargs),
                span_cm,
                stream=stream,
            )

        return wrapped

    return wrapper_factory


def _wrap_amessages(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(
            self: Any,
            model: str,
            messages: object,
            max_tokens: int,
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            stream = bool(kwargs.get("stream"))
            span_cm = layer.span(
                "Run any-llm messages {provider}:{model}",
                provider=self.PROVIDER_NAME,
                model=model,
                stream=stream,
                message_count=safe_count(messages),
                max_tokens=max_tokens,
                tool_count=safe_count(kwargs.get("tools")),
                _span_name="any_llm.messages",
            )
            return await _run_async_call_with_optional_stream(
                lambda: original(self, model, messages, max_tokens, *args, **kwargs),
                span_cm,
                stream=stream,
            )

        return wrapped

    return wrapper_factory


def _wrap_aresponses(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(self: Any, model: str, input_data: object, *args: Any, **kwargs: Any) -> Any:
            stream = bool(kwargs.get("stream"))
            span_cm = layer.span(
                "Run any-llm responses {provider}:{model}",
                provider=self.PROVIDER_NAME,
                model=model,
                stream=stream,
                input_items=_input_items(input_data),
                tool_count=safe_count(kwargs.get("tools")),
                _span_name="any_llm.responses",
            )
            return await _run_async_call_with_optional_stream(
                lambda: original(self, model, input_data, *args, **kwargs),
                span_cm,
                stream=stream,
            )

        return wrapped

    return wrapper_factory


def _wrap_aembedding(layer: logfire.Logfire) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def wrapper_factory(original: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(original)
        async def wrapped(self: Any, model: str, inputs: object, *args: Any, **kwargs: Any) -> Any:
            span_cm = layer.span(
                "Run any-llm embedding {provider}:{model}",
                provider=self.PROVIDER_NAME,
                model=model,
                input_items=_input_items(inputs),
                _span_name="any_llm.embedding",
            )
            with span_cm:
                return await original(self, model, inputs, *args, **kwargs)

        return wrapped

    return wrapper_factory


def instrument_any_llm(
    logfire_instance: logfire.Logfire,
    registry: PatchRegistry,
) -> None:
    from any_llm.any_llm import AnyLLM

    layer = logfire_instance.with_settings(custom_scope_suffix="any_llm", tags=["agentseek", "any-llm"])
    registry.patch(AnyLLM, "create", _wrap_create(layer))
    registry.patch(AnyLLM, "acompletion", _wrap_acompletion(layer))
    registry.patch(AnyLLM, "amessages", _wrap_amessages(layer))
    registry.patch(AnyLLM, "aresponses", _wrap_aresponses(layer))
    registry.patch(AnyLLM, "aembedding", _wrap_aembedding(layer))
