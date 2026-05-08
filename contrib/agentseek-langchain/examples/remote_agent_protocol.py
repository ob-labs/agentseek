from __future__ import annotations

import json
from typing import Any

from agentseek_langchain import AgentProtocolRunnable, AgentProtocolSettings, RunnableBinding
from agentseek_langchain.bridge import LangchainFactoryRequest
from agentseek_langchain.errors import LangchainConfigError
from agentseek_langchain.normalize import to_text
from pydantic import AliasChoices, Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RemoteAgentProtocolExampleConfigError(ValueError):
    """Raised when the bundled remote agent-protocol example is misconfigured."""

    @classmethod
    def missing_url(cls) -> RemoteAgentProtocolExampleConfigError:
        return cls("Set BUB_AGENT_PROTOCOL_URL or AGENTSEEK_AGENT_PROTOCOL_URL for the remote agent-protocol example.")

    @classmethod
    def missing_agent_id(cls) -> RemoteAgentProtocolExampleConfigError:
        return cls(
            "Set BUB_AGENT_PROTOCOL_AGENT_ID or AGENTSEEK_AGENT_PROTOCOL_AGENT_ID for the remote agent-protocol example."
        )


class RemoteAgentProtocolExampleSettings(BaseSettings):
    """Settings for the bundled remote agent-protocol example factory."""

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

    @model_validator(mode="after")
    def _validate_required_fields(self):
        if not self.url.strip():
            raise RemoteAgentProtocolExampleConfigError.missing_url()
        if not self.agent_id.strip():
            raise RemoteAgentProtocolExampleConfigError.missing_agent_id()
        return self


def _load_example_settings() -> AgentProtocolSettings:
    try:
        settings = RemoteAgentProtocolExampleSettings()
    except ValidationError as exc:
        raise LangchainConfigError(str(exc)) from exc
    return AgentProtocolSettings(
        url=settings.url.strip(),
        agent_id=settings.agent_id.strip(),
        api_key=settings.api_key.strip() if isinstance(settings.api_key, str) and settings.api_key.strip() else None,
        stateful=settings.stateful,
    )


def _extract_visible_text_blocks(payload: Any) -> str:
    if isinstance(payload, dict):
        text = payload.get("text")
        return text if isinstance(text, str) else ""
    if not isinstance(payload, list):
        return ""

    parts = [
        text
        for item in payload
        if isinstance(item, dict) and isinstance((text := item.get("text")), str) and text.strip()
    ]
    return "\n".join(parts)


def _parse_remote_agent_output(value: Any) -> str:
    text = to_text(value)
    stripped = text.strip()
    if not stripped or stripped[0] not in "[{":
        return text

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return text

    visible_text = _extract_visible_text_blocks(payload)
    return visible_text or text


def remote_agent_protocol_agent(
    *,
    request: LangchainFactoryRequest,
) -> RunnableBinding:
    """Build a RunnableBinding backed by a user-managed remote agent-protocol server."""

    runnable = AgentProtocolRunnable(
        settings=_load_example_settings(),
        session_id=request.session_id,
        langchain_context=request.langchain_context,
    )
    return RunnableBinding(
        runnable=runnable,
        invoke_input=request.prompt,
        output_parser=_parse_remote_agent_output,
        stream_parser=to_text,
    )
