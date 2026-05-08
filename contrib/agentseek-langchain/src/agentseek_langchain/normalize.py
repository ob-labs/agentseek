from __future__ import annotations

import json
from typing import Any

PREFERRED_TEXT_KEYS = (
    "output",
    "answer",
    "result",
    "final",
    "response",
    "message",
    "text",
)

_PRIMITIVE_TYPES = (str, int, float, bool, type(None))
_MISSING = object()


def _message_content(value: Any) -> Any:
    if hasattr(value, "content"):
        return value.content
    return _MISSING


def normalize_langchain_value(value: Any) -> Any:
    if isinstance(value, _PRIMITIVE_TYPES):
        return value
    if isinstance(value, dict):
        return {str(key): normalize_langchain_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [normalize_langchain_value(item) for item in value]
    if hasattr(value, "model_dump"):
        return normalize_langchain_value(value.model_dump())
    if (content := _message_content(value)) is not _MISSING:
        return normalize_langchain_value(content)
    try:
        json.dumps(value)
    except TypeError:
        return str(value)
    return value


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [normalize_langchain_output(item) for item in content]
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        if isinstance(content.get("text"), str):
            return content["text"]
        return _mapping_to_text(content)
    return str(content)


def _mapping_to_text(data: dict[str, Any]) -> str:
    if "content" in data:
        return _content_to_text(data["content"])

    for key in PREFERRED_TEXT_KEYS:
        if key in data:
            return normalize_langchain_output(data[key])

    messages = data.get("messages")
    if isinstance(messages, list):
        if messages:
            return normalize_langchain_output(messages[-1])
        if "values" in data:
            return normalize_langchain_output(data["values"])
        return ""

    if "values" in data:
        return normalize_langchain_output(data["values"])

    return json.dumps(normalize_langchain_value(data), ensure_ascii=False, default=str)


def normalize_langchain_output(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return _mapping_to_text(value)
    if isinstance(value, list):
        parts = [normalize_langchain_output(item) for item in value]
        return "\n".join(part for part in parts if part)
    if (content := _message_content(value)) is not _MISSING:
        return _content_to_text(content)
    return str(value)
