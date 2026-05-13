from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from agentseek_langchain.spec import InvocationContext, RunnableSpec, default_runnable_config


def _serialize_structured_value(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(), ensure_ascii=False, default=str)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _copilotkit_from_ag_ui_state(state: Mapping[str, object]) -> dict[str, Any] | None:
    items = state.get("ag_ui_context")
    if not isinstance(items, list) or not items:
        return None
    context_items: list[dict[str, Any]] = []
    for raw in items:
        if not isinstance(raw, Mapping):
            continue
        description = raw.get("description")
        value = raw.get("value")
        if not description or value is None:
            continue
        value_str = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
        context_items.append({"description": str(description), "value": value_str})
    if not context_items:
        return None
    return {"actions": [], "context": context_items}


def text_spec(
    runnable: object,
    *,
    input_builder=None,
    output_parser=None,
    config_builder=default_runnable_config,
) -> RunnableSpec:
    return RunnableSpec(
        runnable=runnable,
        build_input=input_builder or _build_text_input,
        parse_output=output_parser or parse_text_output,
        build_config=config_builder,
    )


def messages_spec(
    runnable: object,
    *,
    include_agents_md: bool = False,
    as_state: bool = True,
    messages_key: str = "messages",
    config_builder=default_runnable_config,
) -> RunnableSpec:
    def build_input(context: InvocationContext) -> object:
        messages: list[BaseMessage] = []
        if include_agents_md and context.agents_md:
            messages.append(SystemMessage(content=context.agents_md))
        messages.append(HumanMessage(content=context.prompt))
        if as_state:
            graph_state: dict[str, Any] = {messages_key: messages}
            copilotkit = _copilotkit_from_ag_ui_state(context.state)
            if copilotkit is not None:
                graph_state["copilotkit"] = copilotkit
            return graph_state
        return messages

    def parse_output(result: object) -> str:
        return parse_messages_output(result, messages_key=messages_key)

    return RunnableSpec(
        runnable=runnable,
        build_input=build_input,
        parse_output=parse_output,
        build_config=config_builder,
    )


def parse_text_output(result: object) -> str:
    if isinstance(result, str):
        return result
    if isinstance(result, BaseMessage):
        return _render_message_content(result.content)
    if isinstance(result, Mapping):
        structured = result.get("structured_response")
        if structured is not None:
            return _serialize_structured_value(structured)
        for key in ("output", "result", "text", "final_output"):
            if key in result:
                return parse_text_output(result[key])
        if "messages" in result:
            return _extract_text_from_messages(result["messages"])
    if isinstance(result, list):
        return _extract_text_from_messages(result)
    raise TypeError(f"Unsupported runnable output type: {type(result)!r}")


def parse_messages_output(result: object, *, messages_key: str = "messages") -> str:
    if isinstance(result, Mapping):
        structured = result.get("structured_response")
        if structured is not None:
            return _serialize_structured_value(structured)
        if messages_key in result:
            return _extract_text_from_messages(result[messages_key])
    return parse_text_output(result)


def _build_text_input(context: InvocationContext) -> str:
    if not isinstance(context.prompt, str):
        raise TypeError("text_spec only supports string prompts; use messages_spec for multimodal or messages input")
    return context.prompt


def _extract_text_from_messages(messages: object) -> str:
    if isinstance(messages, BaseMessage):
        return _render_message_content(messages.content)
    if not isinstance(messages, Iterable) or isinstance(messages, (str, bytes)):
        raise TypeError(f"Expected message iterable, got {type(messages)!r}")

    collected = list(messages)
    for message in reversed(collected):
        if isinstance(message, BaseMessage):
            return _render_message_content(message.content)
        if isinstance(message, Mapping):
            content = message.get("content")
            if content is not None:
                return _render_message_content(content)
            if isinstance(message.get("data"), Mapping) and "content" in message["data"]:
                return _render_message_content(message["data"]["content"])
    if not collected:
        return ""
    raise TypeError("Cannot extract text from messages output")


def _render_message_content(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        rendered = [_render_content_block(item) for item in content]
        return "\n".join(part for part in rendered if part)
    if isinstance(content, Mapping):
        if isinstance(content.get("text"), str):
            return str(content["text"])
        return json.dumps(dict(content), ensure_ascii=True, sort_keys=True)
    return str(content)


def _render_content_block(block: object) -> str:
    if isinstance(block, str):
        return block
    if isinstance(block, Mapping):
        if isinstance(block.get("text"), str):
            return str(block["text"])
        return json.dumps(dict(block), ensure_ascii=True, sort_keys=True)
    return str(block)
