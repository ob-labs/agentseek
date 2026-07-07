"""Environment helpers for the {{ cookiecutter.project_name }} LangChain binding."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE = Path(__file__).resolve().parent


class ProjectSettings(BaseSettings):
    """Gateway / OpenAI-style variables for the binding."""

    model_config = SettingsConfigDict(
        env_file=(Path(".env"), _BASE / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    model: str = Field(default="", validation_alias="BUB_MODEL")
    api_key: str = Field(default="", validation_alias="BUB_API_KEY")
    api_base: str = Field(default="", validation_alias="BUB_API_BASE")
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    openai_api_base: str = Field(default="", validation_alias="OPENAI_API_BASE")
    openai_base_url: str = Field(default="", validation_alias="OPENAI_BASE_URL")
    otel_enabled: bool = Field(default=False, validation_alias="AGENTSEEK_OTEL_ENABLED")
    otel_service_name: str = Field(
        default="{{ cookiecutter.project_slug }}",
        validation_alias=AliasChoices("AGENTSEEK_OTEL_SERVICE_NAME", "OTEL_SERVICE_NAME"),
    )
    otel_project_name: str = Field(
        default="{{ cookiecutter.project_slug }}",
        validation_alias=AliasChoices("AGENTSEEK_OTEL_PROJECT_NAME", "OTEL_PROJECT_NAME"),
    )
    otel_traces_endpoint: str = Field(
        default="http://127.0.0.1:6006/v1/traces",
        validation_alias=AliasChoices(
            "AGENTSEEK_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
        ),
    )

    def apply_openai_env_bridge(self) -> None:
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
def get_settings() -> ProjectSettings:
    return ProjectSettings()
