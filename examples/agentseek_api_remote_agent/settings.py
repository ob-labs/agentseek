"""Environment helpers shared by the remote agentseek-api example."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE = Path(__file__).resolve().parent


class AgentSeekApiRemoteExampleSettings(BaseSettings):
    """Settings for both the remote graph and the local bridge."""

    model_config = SettingsConfigDict(
        env_file=(Path(".env"), _BASE / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    model: str = Field(
        default="",
        validation_alias=AliasChoices("AGENTSEEK_MODEL", "BUB_MODEL", "LANGCHAIN_REMOTE_MODEL"),
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
    api_url: str = Field(
        default="http://127.0.0.1:2024",
        validation_alias=AliasChoices("AGENTSEEK_API_REMOTE_URL", "LANGGRAPH_URL"),
    )
    graph_id: str = Field(
        default="agent",
        validation_alias=AliasChoices("AGENTSEEK_API_REMOTE_GRAPH_ID"),
    )
    assistant_name: str = Field(
        default="agentseek-api-demo",
        validation_alias=AliasChoices("AGENTSEEK_API_REMOTE_ASSISTANT_NAME"),
    )
    assistant_id: str = Field(
        default="",
        validation_alias=AliasChoices("AGENTSEEK_API_REMOTE_ASSISTANT_ID", "LANGGRAPH_ASSISTANT_ID"),
    )
    user_id: str = Field(
        default="dev",
        validation_alias=AliasChoices("AGENTSEEK_API_REMOTE_USER_ID"),
    )
    thread_on_session: bool = Field(
        default=False,
        validation_alias=AliasChoices("AGENTSEEK_API_REMOTE_THREAD_ON_SESSION", "LANGGRAPH_THREAD_ON_SESSION"),
    )

    def require_model(self) -> str:
        model = self.model.strip()
        if model:
            return model
        msg = "Set AGENTSEEK_MODEL (or BUB_MODEL / LANGCHAIN_REMOTE_MODEL) for the remote agent process."
        raise RuntimeError(msg)

    def apply_openai_env_bridge(self) -> None:
        model = self.model.strip()
        if not model.lower().startswith("openai:"):
            return

        api_key = self.api_key.strip()
        if api_key and not self.openai_api_key.strip():
            os.environ["OPENAI_API_KEY"] = api_key

        api_base = self.api_base.strip()
        if api_base and not self.openai_api_base.strip() and not self.openai_base_url.strip():
            os.environ["OPENAI_API_BASE"] = api_base

    def request_headers(self) -> dict[str, str]:
        return {"x-user-id": self.user_id}


@lru_cache(maxsize=1)
def get_agentseek_api_remote_settings() -> AgentSeekApiRemoteExampleSettings:
    return AgentSeekApiRemoteExampleSettings()
