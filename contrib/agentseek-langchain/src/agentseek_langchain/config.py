from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LangchainPluginSettings(BaseSettings):
    """Configuration for the agentseek LangChain Runnable adapter."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
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
