from __future__ import annotations

import inspect
import re
from copy import deepcopy
from typing import Any

from bub.tools import REGISTRY
from langchain_core.utils.json_schema import dereference_refs
from republic import Tool, ToolContext


def _sanitize_model_name(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def _args_schema_from_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(parameters, dict) or not parameters:
        return {"type": "object", "properties": {}, "additionalProperties": False}

    if parameters.get("type") != "object":
        return {"type": "object", "properties": {}, "additionalProperties": False}

    schema = _normalize_json_schema(parameters)
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        schema["properties"] = {}
    return schema


def _collect_nested_defs(obj: Any, defs_key: str, collected: dict[str, Any]) -> None:
    if isinstance(obj, dict):
        nested_defs = obj.get(defs_key)
        if isinstance(nested_defs, dict):
            for name, value in nested_defs.items():
                collected.setdefault(name, deepcopy(value))
        for value in obj.values():
            _collect_nested_defs(value, defs_key, collected)
        return
    if isinstance(obj, list):
        for item in obj:
            _collect_nested_defs(item, defs_key, collected)


def _normalize_json_schema(parameters: dict[str, Any]) -> dict[str, Any]:
    schema = deepcopy(parameters)
    for defs_key in ("$defs", "definitions"):
        collected: dict[str, Any] = {}
        _collect_nested_defs(schema, defs_key, collected)
        if collected:
            root_defs = schema.get(defs_key)
            if isinstance(root_defs, dict):
                collected = {**collected, **root_defs}
            schema[defs_key] = collected
    normalized = dereference_refs(schema)
    normalized.pop("$defs", None)
    normalized.pop("definitions", None)
    return normalized


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
