from __future__ import annotations

import inspect
import re
from typing import Any

from bub.tools import REGISTRY
from republic import Tool, ToolContext


def _sanitize_model_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def _args_schema_from_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(parameters, dict) or not parameters:
        return {"type": "object", "properties": {}, "additionalProperties": False}

    if parameters.get("type") != "object":
        return {"type": "object", "properties": {}, "additionalProperties": False}

    schema = dict(parameters)
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        schema["properties"] = {}
    return schema


def bub_tool_to_langchain(bub_tool: Tool, *, tool_context: ToolContext) -> Any:
    from langchain_core.tools import StructuredTool

    async def _async_call(**kwargs: Any) -> Any:
        call_kwargs = dict(kwargs)
        if bub_tool.context:
            call_kwargs["context"] = tool_context
        result = bub_tool.run(**call_kwargs)
        if inspect.isawaitable(result):
            result = await result
        return result

    def _sync_call(**kwargs: Any) -> Any:
        call_kwargs = dict(kwargs)
        if bub_tool.context:
            call_kwargs["context"] = tool_context
        result = bub_tool.run(**call_kwargs)
        if inspect.isawaitable(result):
            raise TypeError(f"Tool {bub_tool.name!r} returned awaitable in sync path")
        return result

    return StructuredTool.from_function(
        func=_sync_call,
        coroutine=_async_call,
        name=_sanitize_model_name(bub_tool.name),
        description=bub_tool.description or bub_tool.name,
        args_schema=_args_schema_from_parameters(bub_tool.parameters),
    )


def bub_registry_to_langchain_tools(
    *,
    tool_context: ToolContext,
    include_names: set[str] | None = None,
) -> list[Any]:
    results: list[Any] = []
    for name, bub_tool in REGISTRY.items():
        if include_names is not None and name not in include_names:
            continue
        results.append(bub_tool_to_langchain(bub_tool, tool_context=tool_context))
    return results
