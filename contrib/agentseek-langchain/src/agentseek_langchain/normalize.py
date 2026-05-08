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


def _prompt_parts_to_text(parts: list[Any]) -> str | None:
    texts: list[str] = []
    saw_prompt_part = False
    for part in parts:
        if not isinstance(part, dict) or "type" not in part:
            continue
        saw_prompt_part = True
        if part.get("type") != "text":
            continue
        text = part.get("text")
        if isinstance(text, str) and text.strip():
            texts.append(text)
    if not saw_prompt_part:
        return None
    return "\n".join(texts).strip()


def to_record(value: Any) -> Any:
    if isinstance(value, _PRIMITIVE_TYPES):
        return value
    if isinstance(value, dict):
        return {str(key): to_record(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [to_record(item) for item in value]
    if hasattr(value, "model_dump"):
        return to_record(value.model_dump())
    if (content := _message_content(value)) is not _MISSING:
        return to_record(content)
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
        parts = [to_text(item) for item in content]
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
            return to_text(data[key])

    messages = data.get("messages")
    if isinstance(messages, list):
        if messages:
            return to_text(messages[-1])
        if "values" in data:
            return to_text(data["values"])
        return ""

    if "values" in data:
        return to_text(data["values"])

    return json.dumps(to_record(data), ensure_ascii=False, default=str)


def to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return _mapping_to_text(value)
    if isinstance(value, list):
        if (prompt_text := _prompt_parts_to_text(value)) is not None:
            return prompt_text
        parts = [to_text(item) for item in value]
        return "\n".join(part for part in parts if part)
    if (content := _message_content(value)) is not _MISSING:
        return _content_to_text(content)
    return str(value)


def to_input(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return to_record(value)
    return {"messages": [{"role": "user", "content": to_text(value)}]}
