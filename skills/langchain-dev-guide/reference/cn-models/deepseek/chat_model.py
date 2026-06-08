"""Custom DeepSeek chat model with reasoning_content preservation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from langchain_core.messages import AIMessage
from langchain_deepseek import ChatDeepSeek as _ChatDeepSeek

if TYPE_CHECKING:
    from langchain_core.language_models import LanguageModelInput


class ChatDeepSeek(_ChatDeepSeek):
    """Custom ChatDeepSeek that fixes reasoning_content preservation.

    The official _get_request_payload handles content list conversion and Azure
    tool_choice correctly, but does NOT write reasoning_content back into AIMessage
    dicts. We preserve all official processing via super() and only inject the
    missing reasoning_content.
    """

    def _get_request_payload(
        self,
        input_: LanguageModelInput,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict:
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        messages = self._convert_input(input_).to_messages()
        for msg_dict, orig_msg in zip(payload["messages"], messages, strict=True):
            if isinstance(orig_msg, AIMessage) and orig_msg.additional_kwargs.get(
                "reasoning_content",
            ):
                msg_dict["reasoning_content"] = orig_msg.additional_kwargs[
                    "reasoning_content"
                ]
        return payload
