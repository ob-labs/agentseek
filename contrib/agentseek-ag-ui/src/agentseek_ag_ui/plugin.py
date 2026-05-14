from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from bub import hookimpl
from bub.types import Envelope, MessageHandler, State

from agentseek_ag_ui.channel import AGUIChannel, _select_message_payload
from agentseek_ag_ui.config import load_settings

AG_UI_INPUT_STATE_KEY = "_ag_ui"


class AGUIPlugin:
    def __init__(self, framework: Any) -> None:
        del framework
        self._channel = AGUIChannel(on_receive=None, settings=load_settings())

    @hookimpl
    def provide_channels(self, message_handler: MessageHandler) -> list[AGUIChannel]:
        self._channel.bind_receiver(message_handler)
        return [self._channel]

    @hookimpl
    def load_state(self, message: Envelope, session_id: str) -> State:
        del session_id
        input_data = self._channel.input_for(message)
        if input_data is None:
            return {}
        loaded = _public_state_from_input_state(input_data.state)
        loaded[AG_UI_INPUT_STATE_KEY] = _transport_state_from_input(input_data)
        return loaded

    @hookimpl(tryfirst=True)
    async def build_prompt(self, message: Envelope, session_id: str, state: State) -> str | list[dict[str, Any]] | None:
        del session_id, state
        input_data = self._channel.input_for(message)
        if input_data is None:
            return None
        content, media = _select_message_payload(input_data.messages)
        context_prefix = _prompt_context_prefix(input_data.context)
        text = f"{context_prefix}\n{content}".strip() if context_prefix else content
        if not media:
            return text

        media_parts: list[dict[str, Any]] = []
        for item in media:
            if item.type == "image" and item.url:
                media_parts.append({"type": "image_url", "image_url": {"url": item.url}})
        if media_parts:
            return [{"type": "text", "text": text}, *media_parts]
        return text

    @hookimpl(trylast=True)
    async def save_state(self, session_id: str, state: State, message: Envelope, model_output: str) -> None:
        del session_id
        if self._channel.input_for(message) is None:
            return
        await self._channel.publish_result(message, state=state, model_output=model_output)

    @hookimpl
    async def on_error(self, stage: str, error: Exception, message: Envelope | None) -> None:
        del stage
        if message is None or self._channel.input_for(message) is None:
            return
        await self._channel.publish_error(
            message,
            error=str(error) or error.__class__.__name__,
            code=type(error).__name__,
        )


def main(framework: Any) -> AGUIPlugin:
    return AGUIPlugin(framework)


def _public_state_from_input_state(value: Any) -> State:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _transport_state_from_input(input_data: Any) -> dict[str, Any]:
    return {
        "messages": _serialize_sequence(input_data.messages),
        "tools": _serialize_sequence(input_data.tools),
        "context": _context_items_from_input(input_data.context),
        "forwarded_props": _serialize_value(getattr(input_data, "forwarded_props", {}) or {}),
    }


def _context_items_from_input(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    context_items: list[dict[str, Any]] = []
    for raw in items:
        if isinstance(raw, Mapping):
            description = raw.get("description")
            value = raw.get("value")
        else:
            description = getattr(raw, "description", None)
            value = getattr(raw, "value", None)
        if not description or value is None:
            continue
        context_items.append({
            "description": str(description),
            "value": _normalize_context_value(value),
        })
    return context_items


def _serialize_sequence(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    serialized: list[dict[str, Any]] = []
    for item in items:
        value = _serialize_value(item)
        if isinstance(value, Mapping):
            serialized.append(dict(value))
    return serialized


def _serialize_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _serialize_value(value.model_dump())
    if hasattr(value, "dict"):
        return _serialize_value(value.dict())
    if isinstance(value, Mapping):
        return {str(key): _serialize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_value(item) for item in value]
    return value


def _prompt_context_prefix(items: Any) -> str:
    context_lines: list[str] = []
    for item in _context_items_from_input(items):
        text_value = _prompt_context_value(item["value"])
        if text_value is None:
            continue
        context_lines.append(f"{item['description']}: {text_value}")
    return "\n".join(context_lines).strip()


def _prompt_context_value(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return None
    text = str(value).strip()
    return text or None


def _normalize_context_value(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value
