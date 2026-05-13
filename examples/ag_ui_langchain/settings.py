"""Environment for the LangChain + CopilotKit-style demo (pydantic-settings)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE = Path(__file__).resolve().parent


class AgUiLangchainDemoSettings(BaseSettings):
    """Gateway / OpenAI-style variables for the demo (env names via ``AliasChoices``)."""

    model_config = SettingsConfigDict(
        env_file=(Path(".env"), _BASE / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    model: str = Field(
        default="",
        validation_alias=AliasChoices("AGENTSEEK_MODEL", "BUB_MODEL"),
    )
    api_key: str = Field(
        default="",
        validation_alias=AliasChoices("AGENTSEEK_API_KEY", "BUB_API_KEY"),
    )
    api_base: str = Field(
        default="",
        validation_alias=AliasChoices("AGENTSEEK_API_BASE", "BUB_API_BASE"),
    )
    openai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_API_KEY"),
    )
    openai_api_base: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_API_BASE"),
    )
    openai_base_url: str = Field(
        default="",
        validation_alias=AliasChoices("OPENAI_BASE_URL"),
    )

    def apply_openai_env_bridge(self) -> None:
        """Copy AgentSeek credentials into ``OPENAI_*`` when the model id uses the ``openai:`` prefix."""
        mid = self.model.strip()
        if not mid.lower().startswith("openai:"):
            return

        seek_key = self.api_key.strip()
        if seek_key and not self.openai_api_key.strip():
            os.environ["OPENAI_API_KEY"] = seek_key

        seek_base = self.api_base.strip()
        if seek_base:
            has_openai_base = bool(self.openai_api_base.strip())
            has_openai_base_url = bool(self.openai_base_url.strip())
            if not has_openai_base and not has_openai_base_url:
                os.environ["OPENAI_API_BASE"] = seek_base


@lru_cache(maxsize=1)
def get_ag_ui_langchain_demo_settings() -> AgUiLangchainDemoSettings:
    return AgUiLangchainDemoSettings()
