from __future__ import annotations

from json import JSONDecodeError
from typing import Any, Self, cast

import openai
from langchain_core.language_models import (
    LanguageModelInput,
    ModelProfile,
    ModelProfileRegistry,
)
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_core.utils import from_env, secret_from_env
from langchain_openai.chat_models.base import BaseChatOpenAI, _convert_message_to_dict
from pydantic import Field, SecretStr, model_validator

_INVALID_RESPONSE_ERROR_MSG = (
    "Provider API returned an invalid response. "
    "Please check your API key, network connection, or API base URL."
)


def _get_default_model_profile(model_name: str) -> ModelProfile:
    try:
        from .data._profiles import _PROFILES  # type: ignore[import-untyped]
    except ImportError:
        return {}

    _MODEL_PROFILES = cast("ModelProfileRegistry", _PROFILES)
    default = _MODEL_PROFILES.get(model_name) or {}
    return default.copy()


class ChatModel(BaseChatOpenAI):
    api_key: SecretStr | None = Field(
        default_factory=secret_from_env("PROVIDER_API_KEY", default=None),
    )
    api_base: str = Field(
        default_factory=from_env(
            "PROVIDER_API_BASE",
            default="PROVIDER_API_BASE_URL",
        ),
    )

    @property
    def _llm_type(self) -> str:
        return "chat-provider"

    @property
    def lc_secrets(self) -> dict[str, str]:
        return {"api_key": "PROVIDER_API_KEY"}

    @model_validator(mode="after")
    def validate_environment(self) -> Self:
        if not (self.api_key and self.api_key.get_secret_value()):
            msg = "PROVIDER_API_KEY must be set."
            raise ValueError(msg)
        client_params: dict = {
            "api_key": self.api_key.get_secret_value() if self.api_key else None,
            "base_url": self.api_base,
            "timeout": self.request_timeout,
            "max_retries": self.max_retries,
            "default_headers": self.default_headers,
            "default_query": self.default_query,
        }
        client_params = {k: v for k, v in client_params.items() if v is not None}
        if not (self.client or None):
            sync_specific: dict = {"http_client": self.http_client}
            self.root_client = openai.OpenAI(**client_params, **sync_specific)
            self.client = self.root_client.chat.completions
        if not (self.async_client or None):
            async_specific: dict = {"http_client": self.http_async_client}
            self.root_async_client = openai.AsyncOpenAI(
                **client_params, **async_specific,
            )
            self.async_client = self.root_async_client.chat.completions
        return self

    def _resolve_model_profile(self) -> ModelProfile | None:
        return _get_default_model_profile(self.model_name) or None

    def _get_request_payload(
        self,
        input_: LanguageModelInput,
        *,
        stop: list[str] | None = None,
        **kwargs: Any,
    ) -> dict:
        payload = super()._get_request_payload(input_, stop=stop, **kwargs)
        messages = self._convert_input(input_).to_messages()
        payload_messages = []
        for m in messages:
            if isinstance(m, AIMessage):
                msg_dict = _convert_message_to_dict(m)
                if m.additional_kwargs.get("reasoning_content"):
                    msg_dict["reasoning_content"] = m.additional_kwargs.get(
                        "reasoning_content",
                    )
                payload_messages.append(msg_dict)
            else:
                payload_messages.append(_convert_message_to_dict(m))
        payload["messages"] = payload_messages
        if "tools" in payload and len(payload["tools"]) == 0:
            payload.pop("tools")
        return payload

    def _create_chat_result(
        self,
        response: dict | openai.BaseModel,
        generation_info: dict | None = None,
    ) -> ChatResult:
        rtn = super()._create_chat_result(response, generation_info)
        if isinstance(response, openai.BaseModel):
            choices = getattr(response, "choices", None)
            if choices and hasattr(choices[0].message, "reasoning_content"):
                rtn.generations[0].message.additional_kwargs["reasoning_content"] = (
                    choices[0].message.reasoning_content
                )
        return rtn

    def _convert_chunk_to_generation_chunk(
        self,
        chunk: dict,
        default_chunk_class: type,
        base_generation_info: dict | None,
    ) -> ChatGenerationChunk | None:
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk,
            default_chunk_class,
            base_generation_info,
        )
        if (choices := chunk.get("choices")) and generation_chunk:
            top = choices[0]
            if isinstance(generation_chunk.message, AIMessageChunk) and (
                reasoning_content := top.get("delta", {}).get("reasoning_content")
            ) is not None:
                generation_chunk.message.additional_kwargs["reasoning_content"] = (
                    reasoning_content
                )
        return generation_chunk

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        kwargs["stream_options"] = {"include_usage": True}
        try:
            yield from super()._stream(
                messages, stop=stop, run_manager=run_manager, **kwargs,
            )
        except JSONDecodeError as e:
            raise JSONDecodeError(
                _INVALID_RESPONSE_ERROR_MSG,
                e.doc,
                e.pos,
            ) from e

    async def _astream(self, messages, stop=None, run_manager=None, **kwargs):
        kwargs["stream_options"] = {"include_usage": True}
        try:
            async for chunk in super()._astream(
                messages, stop=stop, run_manager=run_manager, **kwargs,
            ):
                yield chunk
        except JSONDecodeError as e:
            raise JSONDecodeError(
                _INVALID_RESPONSE_ERROR_MSG,
                e.doc,
                e.pos,
            ) from e

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        try:
            return super()._generate(
                messages, stop=stop, run_manager=run_manager, **kwargs,
            )
        except JSONDecodeError as e:
            raise JSONDecodeError(
                _INVALID_RESPONSE_ERROR_MSG,
                e.doc,
                e.pos,
            ) from e

    async def _agenerate(self, messages, stop=None, run_manager=None, **kwargs):
        try:
            return await super()._agenerate(
                messages, stop=stop, run_manager=run_manager, **kwargs,
            )
        except JSONDecodeError as e:
            raise JSONDecodeError(
                _INVALID_RESPONSE_ERROR_MSG,
                e.doc,
                e.pos,
            ) from e
