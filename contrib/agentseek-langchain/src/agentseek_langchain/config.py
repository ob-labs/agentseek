from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, Field
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


def load_settings() -> LangchainPluginSettings:
    return LangchainPluginSettings()


def is_enabled(settings: LangchainPluginSettings) -> bool:
    return settings.mode == "runnable"


def validate_config(settings: LangchainPluginSettings) -> None:
    """Raise :class:`LangchainConfigError` when required variables are missing."""

    if settings.mode == "runnable" and not settings.factory:
        raise LangchainConfigError("BUB_LANGCHAIN_FACTORY is required in runnable mode")
