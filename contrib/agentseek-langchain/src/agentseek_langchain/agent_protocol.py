from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator, Mapping
from typing import Any, Self

from langchain_core.runnables import Runnable, RunnableConfig
from loguru import logger
from pydantic import AliasChoices, Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .bridge import LangchainRunContext
from .errors import LangchainConfigError
from .normalize import to_input, to_text

INTERRUPT_KEY = "__interrupt__"


class AgentProtocolSettings(BaseSettings):
    """Configuration for the remote agent-protocol runnable adapter."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    url: str = Field(
        default="",
        validation_alias=AliasChoices("BUB_AGENT_PROTOCOL_URL", "AGENTSEEK_AGENT_PROTOCOL_URL"),
    )
    agent_id: str = Field(
        default="",
        validation_alias=AliasChoices("BUB_AGENT_PROTOCOL_AGENT_ID", "AGENTSEEK_AGENT_PROTOCOL_AGENT_ID"),
    )

    @model_validator(mode="after")
    def _require_url_and_agent_id(self) -> Self:
        if not self.url.strip():
            raise ValueError(
                "Set BUB_AGENT_PROTOCOL_URL or AGENTSEEK_AGENT_PROTOCOL_URL (remote agent-protocol base URL)."
            )
        if not self.agent_id.strip():
            raise ValueError("Set BUB_AGENT_PROTOCOL_AGENT_ID or AGENTSEEK_AGENT_PROTOCOL_AGENT_ID (remote agent id).")
        return self

    api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "BUB_AGENT_PROTOCOL_API_KEY",
            "AGENTSEEK_AGENT_PROTOCOL_API_KEY",
            "BUB_API_KEY",
            "AGENTSEEK_API_KEY",
        ),
    )
    stateful: bool = Field(
        default=True,
        validation_alias=AliasChoices("BUB_AGENT_PROTOCOL_STATEFUL", "AGENTSEEK_AGENT_PROTOCOL_STATEFUL"),
    )


def load_agent_protocol_settings() -> AgentProtocolSettings:
    try:
        return AgentProtocolSettings()
    except ValidationError as exc:
        raise LangchainConfigError(str(exc)) from exc


class AgentProtocolRemoteError(RuntimeError):
    """Raised when the remote agent-protocol run returns an explicit error event."""


class AgentProtocolInterruptedError(RuntimeError):
    """Raised when the remote agent-protocol run reports an interrupt."""


class AgentProtocolRunnable(Runnable[Any, Any]):
    """Wrap a remote Bub agent-protocol endpoint as a Bub-oriented Runnable.

    This adapter intentionally accepts Bub prompt shapes or a fully-formed input
    dict. It does not implement general Pregel or RemoteGraph config semantics.
    """

    def __init__(
        self,
        *,
        settings: AgentProtocolSettings,
        session_id: str | None,
        langchain_context: LangchainRunContext | None = None,
    ) -> None:
        self._settings = settings
        self._session_id = session_id
        self._langchain_context = langchain_context
        self._logger = logger if langchain_context is None else logger.bind(**langchain_context.as_logger_extra())
        self._client: Any | None = None

    def invoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:  # noqa: A002
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.ainvoke(input, config=config, **kwargs))
        raise RuntimeError("AgentProtocolRunnable.invoke cannot be used from a running event loop; use ainvoke instead")

    async def ainvoke(self, input: Any, config: RunnableConfig | None = None, **kwargs: Any) -> Any:  # noqa: A002
        thread_id = self._default_thread_id() if self._settings.stateful and self._session_id else None
        metadata = self._build_metadata(config)
        self._logger.debug(
            "Invoking remote agent-protocol agent={} stateful={} thread_id={}",
            self._settings.agent_id,
            self._settings.stateful,
            thread_id,
        )
        return await self._client_instance().runs.wait(
            thread_id=thread_id,
            assistant_id=self._settings.agent_id,
            input=to_input(input),
            metadata=metadata,
            if_not_exists="create" if thread_id is not None else None,
        )

    @staticmethod
    def _stream_event(part: Any) -> tuple[str | None, Any]:
        event = None
        data = None
        if hasattr(part, "event"):
            raw_event = part.event
            event = raw_event if isinstance(raw_event, str) else None
        elif isinstance(part, dict):
            raw_event = part.get("event") or part.get("type")
            event = raw_event if isinstance(raw_event, str) else None

        if hasattr(part, "data"):
            data = part.data
        elif isinstance(part, dict):
            data = part.get("data")
        return event, data

    @staticmethod
    def _stream_interrupts(part: Any, data: Any) -> list[Any]:
        if isinstance(part, dict):
            raw_interrupts = part.get("interrupts")
            if isinstance(raw_interrupts, list) and raw_interrupts:
                return raw_interrupts
        if isinstance(data, Mapping):
            raw_interrupts = data.get(INTERRUPT_KEY)
            if isinstance(raw_interrupts, list) and raw_interrupts:
                return raw_interrupts
        return []

    @staticmethod
    def _raise_for_stream_issue(event: str | None, data: Any, interrupts: list[Any]) -> None:
        if event is not None and event.startswith("error"):
            detail = to_text(data)
            raise AgentProtocolRemoteError(detail or "Remote agent-protocol run failed")

        if interrupts and event is not None and (event == "values" or event.startswith("updates")):
            raise AgentProtocolInterruptedError(
                f"Remote agent-protocol run interrupted: {json.dumps(interrupts, ensure_ascii=False, default=str)}"
            )

    @staticmethod
    def _stream_messages(
        event: str | None,
        data: Any,
        *,
        saw_partial_message: bool,
    ) -> tuple[list[Mapping[str, Any]], bool]:
        if event == "messages/complete" and saw_partial_message:
            return [], saw_partial_message
        if event == "messages":
            if isinstance(data, list) and data and isinstance(data[0], Mapping):
                return [data[0]], saw_partial_message
            return [], saw_partial_message
        if event == "messages/partial":
            saw_partial_message = True
        if event in {"messages/partial", "messages/complete"} and isinstance(data, list):
            return [item for item in data if isinstance(item, Mapping)], saw_partial_message
        return [], saw_partial_message

    @staticmethod
    def _assistant_text(message: Mapping[str, Any]) -> str | None:
        role = None
        for key in ("role", "type"):
            value = message.get(key)
            if isinstance(value, str) and value.strip():
                role = value.strip().lower()
                break
        if role is not None and role not in {"assistant", "ai", "aimessage", "aimessagechunk"}:
            return None
        text = to_text(dict(message))
        return text or None

    async def astream(
        self,
        input: Any,  # noqa: A002
        config: RunnableConfig | None = None,
        **kwargs: Any | None,
    ) -> AsyncIterator[str]:
        thread_id = self._default_thread_id() if self._settings.stateful and self._session_id else None
        metadata = self._build_metadata(config)
        self._logger.debug(
            "Streaming remote agent-protocol agent={} stateful={} thread_id={}",
            self._settings.agent_id,
            self._settings.stateful,
            thread_id,
        )
        emitted = False
        saw_partial_message = False
        final_state: Any | None = None
        async for part in self._client_instance().runs.stream(
            thread_id=thread_id,
            assistant_id=self._settings.agent_id,
            input=to_input(input),
            metadata=metadata,
            if_not_exists="create" if thread_id is not None else None,
            stream_mode=["messages", "values", "updates"],
        ):
            event, data = self._stream_event(part)
            interrupts = self._stream_interrupts(part, data)
            self._raise_for_stream_issue(event, data, interrupts)

            if event == "values":
                final_state = data

            messages, saw_partial_message = self._stream_messages(
                event,
                data,
                saw_partial_message=saw_partial_message,
            )

            for message in messages:
                text = self._assistant_text(message)
                if text is None:
                    continue
                emitted = True
                yield text

        if not emitted and final_state is not None:
            fallback_text = to_text(final_state)
            if fallback_text:
                yield fallback_text

    def _client_instance(self) -> Any:
        if self._client is None:
            from langgraph_sdk import get_client

            client_kwargs: dict[str, Any] = {"url": self._settings.url}
            if self._settings.api_key is not None:
                client_kwargs["api_key"] = self._settings.api_key
            self._client = get_client(**client_kwargs)
        return self._client

    def _build_metadata(self, config: Mapping[str, Any] | None) -> dict[str, Any]:
        metadata: dict[str, Any] = {}
        if self._langchain_context is not None:
            metadata.update(self._langchain_context.as_metadata())

        if not isinstance(config, Mapping):
            return metadata

        config_metadata = config.get("metadata")
        if not isinstance(config_metadata, Mapping):
            return metadata

        for key, value in config_metadata.items():
            if isinstance(key, str):
                metadata[key] = value
        return metadata

    def _default_thread_id(self) -> str:
        payload = f"{self._settings.url}\0{self._settings.agent_id}\0{self._session_id}"
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
        return f"agentseek-{digest}"
