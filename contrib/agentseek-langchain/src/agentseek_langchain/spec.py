from __future__ import annotations

import asyncio
import inspect
from collections.abc import AsyncIterator, Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class InvocationContext:
    prompt: str | list[dict[str, Any]]
    session_id: str
    state: Mapping[str, object]
    workspace: Path
    agents_md: str | None
    # LangGraph runtime context, e.g. CopilotKit ``output_schema`` binding.
    runtime_context: Mapping[str, object] | None = None


InputBuilder = Callable[[InvocationContext], object]
OutputParser = Callable[[object], str]
ConfigBuilder = Callable[[InvocationContext], Mapping[str, object] | None]
StreamBuilder = Callable[[object, object, Mapping[str, object] | None, InvocationContext], AsyncIterator[str]]


@runtime_checkable
class AsyncRunnable(Protocol):
    def ainvoke(self, runnable_input: object, /, **kwargs: object) -> object: ...


@runtime_checkable
class SyncRunnable(Protocol):
    def invoke(self, runnable_input: object, /, **kwargs: object) -> object: ...


@dataclass(frozen=True, slots=True)
class RunnableSpec:
    runnable: object
    build_input: InputBuilder
    parse_output: OutputParser
    build_config: ConfigBuilder = lambda _context: default_runnable_config(_context)
    stream_output: StreamBuilder | None = None

    async def invoke(self, context: InvocationContext) -> str:
        runnable_input, config = self._prepare(context)
        result = await invoke_runnable(self.runnable, runnable_input, config, runtime_context=context.runtime_context)
        return self.parse_output(result)

    async def stream(self, context: InvocationContext) -> AsyncIterator[str]:
        runnable_input, config = self._prepare(context)
        if self.stream_output is None:
            yield self.parse_output(
                await invoke_runnable(self.runnable, runnable_input, config, runtime_context=context.runtime_context)
            )
            return
        async for chunk in self.stream_output(self.runnable, runnable_input, config, context):
            yield chunk

    def _prepare(self, context: InvocationContext) -> tuple[object, Mapping[str, object] | None]:
        return self.build_input(context), self.build_config(context)


def default_runnable_config(context: InvocationContext) -> Mapping[str, object]:
    return {
        "run_name": "agentseek",
        "tags": ["agentseek"],
        "metadata": {
            "session_id": context.session_id,
            "workspace": str(context.workspace),
        },
        "configurable": {
            "session_id": context.session_id,
            "thread_id": context.session_id,
        },
    }


async def invoke_runnable(
    runnable: object,
    runnable_input: object,
    config: Mapping[str, object] | None = None,
    *,
    runtime_context: Mapping[str, object] | None = None,
) -> object:
    if isinstance(runnable, AsyncRunnable):
        result = _call_runnable_method(runnable.ainvoke, runnable_input, config, runtime_context)
        if inspect.isawaitable(result):
            return await result
        return result
    if isinstance(runnable, SyncRunnable):
        return await asyncio.to_thread(_call_runnable_method, runnable.invoke, runnable_input, config, runtime_context)
    raise TypeError("Runnable object must define invoke() or ainvoke()")


def _call_runnable_method(
    method: Callable[..., object],
    runnable_input: object,
    config: Mapping[str, object] | None,
    runtime_context: Mapping[str, object] | None,
) -> object:
    kwargs: dict[str, object] = {}
    if config is not None and _supports_config_argument(method):
        kwargs["config"] = config
    if runtime_context is not None and _supports_context_argument(method):
        kwargs["context"] = runtime_context
    if kwargs:
        return method(runnable_input, **kwargs)
    return method(runnable_input)


def _supports_config_argument(method: Callable[..., object]) -> bool:
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return True
    for parameter in signature.parameters.values():
        if parameter.kind is inspect.Parameter.VAR_KEYWORD:
            return True
        if parameter.name == "config":
            return True
    return False


def _supports_context_argument(method: Callable[..., object]) -> bool:
    try:
        signature = inspect.signature(method)
    except (TypeError, ValueError):
        return True
    for parameter in signature.parameters.values():
        if parameter.kind is inspect.Parameter.VAR_KEYWORD:
            return True
        if parameter.name == "context":
            return True
    return False
