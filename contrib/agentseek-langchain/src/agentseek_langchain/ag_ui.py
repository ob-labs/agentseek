from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage

from agentseek_langchain.shapes import HumanMessageContent, ObjectDict, StrMapping, as_str_mapping, copy_str_mapping

AG_UI_INPUT_STATE_KEY = "_ag_ui"
_MESSAGES_FIELD = "messages"
_TOOLS_FIELD = "tools"
_CONTEXT_FIELD = "context"
_DESCRIPTION_FIELD = "description"
_VALUE_FIELD = "value"
_ROLE_FIELD = "role"
_ID_FIELD = "id"
_NAME_FIELD = "name"
_CONTENT_FIELD = "content"
_TYPE_FIELD = "type"
_TEXT_FIELD = "text"


def ag_ui_input_from_state(state: Mapping[str, object]) -> StrMapping | None:
    return as_str_mapping(state.get(AG_UI_INPUT_STATE_KEY))


def application_state_from_state(state: Mapping[str, object]) -> dict[str, object]:
    return {str(key): value for key, value in state.items() if isinstance(key, str) and not key.startswith("_")}


def ag_ui_context_items_from_state(state: Mapping[str, object]) -> list[tuple[str, object]]:
    ag_ui_input = ag_ui_input_from_state(state)
    if ag_ui_input is None:
        return []

    raw_items = ag_ui_input.get(_CONTEXT_FIELD)
    if not isinstance(raw_items, list):
        return []

    items: list[tuple[str, object]] = []
    for raw_item in raw_items:
        item = as_str_mapping(raw_item)
        if item is None:
            continue
        description = item.get(_DESCRIPTION_FIELD)
        if not isinstance(description, str) or not description:
            continue
        value = normalize_context_value(item.get(_VALUE_FIELD))
        if value is None:
            continue
        items.append((description, value))
    return items


def runtime_context_from_state(state: Mapping[str, object]) -> Mapping[str, object] | None:
    items = ag_ui_context_items_from_state(state)
    if not items:
        return None
    return dict(items)


def copilotkit_state_from_state(state: Mapping[str, object]) -> dict[str, object] | None:
    actions = ag_ui_tools_from_state(state)
    context_items = ag_ui_context_items_from_state(state)

    if not actions and not context_items:
        return None

    copilot_context = [
        {
            "description": description,
            "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value),
        }
        for description, value in context_items
    ]
    return {
        "actions": actions,
        "context": copilot_context,
    }


def ag_ui_tools_from_state(state: Mapping[str, object]) -> list[ObjectDict]:
    ag_ui_input = ag_ui_input_from_state(state)
    if ag_ui_input is None:
        return []

    raw_tools = ag_ui_input.get(_TOOLS_FIELD)
    if not isinstance(raw_tools, list):
        return []
    tools: list[ObjectDict] = []
    for raw_tool in raw_tools:
        if (tool := copy_str_mapping(raw_tool)) is not None:
            tools.append(tool)
    return tools


def langchain_messages_from_state(state: Mapping[str, object]) -> list[BaseMessage]:
    ag_ui_input = ag_ui_input_from_state(state)
    if ag_ui_input is None:
        return []

    raw_messages = ag_ui_input.get(_MESSAGES_FIELD)
    if not isinstance(raw_messages, list):
        return []
    return ag_ui_messages_to_langchain(raw_messages)


def ag_ui_messages_to_langchain(messages: Sequence[object]) -> list[BaseMessage]:
    langchain_messages: list[BaseMessage] = []
    for raw_message in messages:
        message = as_str_mapping(raw_message)
        if message is None:
            continue
        role = message.get(_ROLE_FIELD)
        if not isinstance(role, str):
            continue

        if role in {"reasoning", "developer", "activity"}:
            continue

        message_id = _optional_string(message.get(_ID_FIELD))
        name = _optional_string(message.get(_NAME_FIELD))
        content = message.get(_CONTENT_FIELD)

        if role == "user":
            langchain_messages.append(
                HumanMessage(
                    id=message_id,
                    name=name,
                    content=_user_content_to_langchain(content),
                )
            )
            continue

        if role == "assistant":
            langchain_messages.append(
                AIMessage(
                    id=message_id,
                    name=name,
                    content="" if content is None else str(content),
                    tool_calls=_assistant_tool_calls_to_langchain(message.get("tool_calls")),
                )
            )
            continue

        if role == "system":
            langchain_messages.append(
                SystemMessage(
                    id=message_id,
                    name=name,
                    content="" if content is None else str(content),
                )
            )
            continue

        if role == "tool":
            tool_call_id = _optional_string(message.get("tool_call_id"))
            if not tool_call_id:
                continue
            langchain_messages.append(
                ToolMessage(
                    id=message_id,
                    tool_call_id=tool_call_id,
                    content=_tool_content_to_text(content),
                )
            )

    return langchain_messages


def normalize_context_value(value: object) -> object:
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _user_content_to_langchain(content: object) -> HumanMessageContent:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        converted: list[str | dict[str, object]] = []
        for item in content:
            if (part := _content_part_to_langchain(item)) is not None:
                converted.append(part)
        return converted
    return "" if content is None else str(content)


def _content_part_to_langchain(item: object) -> ObjectDict | None:
    part = as_str_mapping(item)
    if part is None:
        return None

    part_type = part.get(_TYPE_FIELD)
    if part_type == "text":
        text = part.get(_TEXT_FIELD)
        return {_TYPE_FIELD: _TEXT_FIELD, _TEXT_FIELD: "" if text is None else str(text)}

    if part_type == "binary":
        url = _binary_item_to_url(part)
        if url is None:
            return None
        return {_TYPE_FIELD: "image_url", "image_url": {"url": url}}

    if part_type in {"image", "audio", "video", "document"}:
        source = part.get("source")
        url = _source_to_url(source)
        if url is None:
            return None
        return {_TYPE_FIELD: "image_url", "image_url": {"url": url}}

    return None


def _source_to_url(source: object) -> str | None:
    source_mapping = as_str_mapping(source)
    if source_mapping is None:
        return None
    source_type = source_mapping.get(_TYPE_FIELD)
    value = source_mapping.get(_VALUE_FIELD)
    if not isinstance(value, str) or not value:
        return None

    if source_type == "url":
        return value

    if source_type == "data":
        mime_type = source_mapping.get("mime_type") or source_mapping.get("mimeType") or "application/octet-stream"
        return f"data:{mime_type};base64,{value}"

    return None


def _binary_item_to_url(item: StrMapping) -> str | None:
    url = item.get("url")
    if isinstance(url, str) and url:
        return url

    data = item.get("data")
    if isinstance(data, str) and data:
        mime_type = item.get("mime_type") or item.get("mimeType") or "application/octet-stream"
        return f"data:{mime_type};base64,{data}"

    item_id = item.get("id")
    if isinstance(item_id, str) and item_id:
        return item_id
    return None


def _assistant_tool_calls_to_langchain(raw_tool_calls: object) -> list[dict[str, object]]:
    if not isinstance(raw_tool_calls, list):
        return []

    tool_calls: list[dict[str, object]] = []
    for raw_tool_call in raw_tool_calls:
        tool_call = as_str_mapping(raw_tool_call)
        if tool_call is None:
            continue
        function = as_str_mapping(tool_call.get("function"))
        if function is None:
            continue

        call_id = _optional_string(tool_call.get(_ID_FIELD))
        name = _optional_string(function.get(_NAME_FIELD))
        if not call_id or not name:
            continue

        raw_arguments = function.get("arguments")
        arguments = _decode_json_object(raw_arguments)
        tool_calls.append({
            "id": call_id,
            "name": name,
            "args": arguments,
            "type": "tool_call",
        })

    return tool_calls


def _decode_json_object(value: object) -> object:
    if value is None:
        return {}
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    if (mapping := copy_str_mapping(value)) is not None:
        return mapping
    return {}


def _tool_content_to_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
                continue
            block_mapping = as_str_mapping(block)
            if block_mapping is not None and block_mapping.get(_TYPE_FIELD) == _TEXT_FIELD:
                text = block_mapping.get(_TEXT_FIELD)
                parts.append("" if text is None else str(text))
                continue
            parts.append(json.dumps(block, ensure_ascii=False))
        return "".join(parts)
    return "" if content is None else json.dumps(content, ensure_ascii=False)
