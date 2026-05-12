from __future__ import annotations

from typing import Any

from bub import hookimpl
from bub.types import Envelope, MessageHandler, State

from agentseek_ag_ui.channel import AGUIChannel, _select_message_payload
from agentseek_ag_ui.config import load_settings


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
        if isinstance(input_data.state, dict):
            return {"ag_ui": dict(input_data.state)}
        if input_data.state is None:
            return {}
        return {"ag_ui": input_data.state}

    @hookimpl(tryfirst=True)
    async def build_prompt(self, message: Envelope, session_id: str, state: State) -> str | list[dict[str, Any]] | None:
        del session_id, state
        input_data = self._channel.input_for(message)
        if input_data is None:
            return None
        content, media = _select_message_payload(input_data.messages)
        context_prefix = "\n".join(
            f"{item.description}: {item.value}" for item in input_data.context if item.description and item.value
        ).strip()
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
