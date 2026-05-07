from __future__ import annotations

from typing import Any, Literal, cast

from pydantic import AliasChoices, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from .errors import LangchainConfigError


class LangchainPluginSettings(BaseSettings):
    """Configuration for the agentseek LangChain Runnable adapter."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    mode: Literal["", "runnable"] = Field(
        default="",
        validation_alias=AliasChoices("BUB_LANGCHAIN_MODE", "AGENTSEEK_LANGCHAIN_MODE"),
    )
    factory: str | None = Field(
        default=None,
        validation_alias=AliasChoices("BUB_LANGCHAIN_FACTORY", "AGENTSEEK_LANGCHAIN_FACTORY"),
    )
    include_bub_tools: bool = Field(
        default=True,
        validation_alias=AliasChoices("BUB_LANGCHAIN_INCLUDE_BUB_TOOLS", "AGENTSEEK_LANGCHAIN_INCLUDE_BUB_TOOLS"),
    )
    tape: bool = Field(
        default=True,
        validation_alias=AliasChoices("BUB_LANGCHAIN_TAPE", "AGENTSEEK_LANGCHAIN_TAPE"),
    )


class AgentProtocolSettings(BaseSettings):
    """Configuration for the remote agent-protocol runnable adapter."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    url: str = Field(
        validation_alias=AliasChoices("BUB_AGENT_PROTOCOL_URL", "AGENTSEEK_AGENT_PROTOCOL_URL"),
    )
    agent_id: str = Field(
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


def load_settings() -> LangchainPluginSettings:
    return LangchainPluginSettings()


def load_agent_protocol_settings() -> AgentProtocolSettings:
    try:
        settings_cls = cast(Any, AgentProtocolSettings)
        return cast(AgentProtocolSettings, settings_cls())
    except ValidationError as exc:
        raise LangchainConfigError(str(exc)) from exc


def is_enabled(settings: LangchainPluginSettings) -> bool:
    return settings.mode == "runnable"


def validate_config(settings: LangchainPluginSettings) -> None:
    """Raise :class:`LangchainConfigError` when required variables are missing."""

    if settings.mode == "runnable" and not settings.factory:
        raise LangchainConfigError("BUB_LANGCHAIN_FACTORY is required in runnable mode")
