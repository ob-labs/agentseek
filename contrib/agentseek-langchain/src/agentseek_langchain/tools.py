from __future__ import annotations

import inspect
from functools import wraps
from typing import Any

from bub.tools import REGISTRY
from langchain_core.tools import tool as langchain_tool
from republic import Tool, ToolContext

from .errors import LangchainConfigError


def bub_tool_to_langchain(
    bub_tool: Tool,
    *,
    tool_context: ToolContext,
    tool_name: str | None = None,
) -> Any:
    handler = bub_tool.handler
    if handler is None:
        raise LangchainConfigError(f"Tool {bub_tool.name!r} is schema-only and cannot be executed")

    for cell in getattr(handler, "__closure__", None) or ():
        value = cell.cell_contents
        if isinstance(value, Tool) and value.handler is not None:
            handler = value.handler
            break

    signature = inspect.signature(handler)
    if bub_tool.context:
        signature = signature.replace(
            parameters=[parameter for parameter in signature.parameters.values() if parameter.name != "context"]
        )

    if inspect.iscoroutinefunction(handler):

        @wraps(handler)
        async def callable_handler(*args: Any, **kwargs: Any) -> Any:
            if bub_tool.context:
                kwargs["context"] = tool_context
            return await handler(*args, **kwargs)

    else:

        @wraps(handler)
        def callable_handler(*args: Any, **kwargs: Any) -> Any:
            if bub_tool.context:
                kwargs["context"] = tool_context
            return handler(*args, **kwargs)

    wrapped_handler: Any = callable_handler
    wrapped_handler.__signature__ = signature
    return langchain_tool(
        tool_name or bub_tool.name,
        description=bub_tool.description or bub_tool.name,
    )(wrapped_handler)


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
