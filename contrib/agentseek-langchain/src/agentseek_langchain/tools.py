from __future__ import annotations

import inspect
from functools import wraps
from typing import Any

from bub.tools import REGISTRY
from langchain_core.tools import tool as langchain_tool
from republic import Tool, ToolContext

from .errors import LangchainConfigError


def _raw_bub_handler(bub_tool: Tool) -> Any:
    handler = bub_tool.handler
    if handler is None:
        raise LangchainConfigError(f"Tool {bub_tool.name!r} is schema-only and cannot be executed")

    closure = getattr(handler, "__closure__", None)
    for cell in closure or ():
        value = cell.cell_contents
        if isinstance(value, Tool) and value.handler is not None:
            return value.handler
    return handler


def _call_signature(handler: Any, *, with_context: bool) -> inspect.Signature:
    signature = inspect.signature(handler)
    if with_context:
        return signature
    parameters = [parameter for parameter in signature.parameters.values() if parameter.name != "context"]
    return signature.replace(parameters=parameters)


def _langchain_callable(bub_tool: Tool, tool_context: ToolContext) -> Any:
    handler = _raw_bub_handler(bub_tool)
    signature = _call_signature(handler, with_context=not bub_tool.context)

    if inspect.iscoroutinefunction(handler):

        @wraps(handler)
        async def _call(*args: Any, **kwargs: Any) -> Any:
            if bub_tool.context:
                kwargs["context"] = tool_context
            return await handler(*args, **kwargs)

    else:

        @wraps(handler)
        def _call(*args: Any, **kwargs: Any) -> Any:
            if bub_tool.context:
                kwargs["context"] = tool_context
            return handler(*args, **kwargs)

    wrapped: Any = _call
    wrapped.__signature__ = signature
    return _call


def bub_tool_to_langchain(
    bub_tool: Tool,
    *,
    tool_context: ToolContext,
    tool_name: str | None = None,
) -> Any:
    return langchain_tool(
        tool_name or bub_tool.name,
        description=bub_tool.description or bub_tool.name,
    )(_langchain_callable(bub_tool, tool_context))


def bub_registry_to_langchain_tools(
    *,
    tool_context: ToolContext,
    include_names: set[str] | None = None,
) -> list[Any]:
    results: list[Any] = []
    for registry_name, bub_tool in REGISTRY.items():
        if include_names is not None and registry_name not in include_names:
            continue
        results.append(bub_tool_to_langchain(bub_tool, tool_context=tool_context))
    return results
