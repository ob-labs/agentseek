"""Settings for the LangChain OTEL sidecar example."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE = Path(__file__).resolve().parent


class LangChainOtelSidecarSettings(BaseSettings):
    """Runtime settings shared by the demo app and helper commands."""

    model_config = SettingsConfigDict(
        env_file=(Path(".env"), _BASE / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    model: str = Field(
        default="",
        validation_alias=AliasChoices(
            "LANGCHAIN_OTEL_DEMO_MODEL",
            "AGENTSEEK_MODEL",
            "BUB_MODEL",
        ),
    )
    api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "LANGCHAIN_OTEL_DEMO_API_KEY",
            "AGENTSEEK_API_KEY",
            "BUB_API_KEY",
        ),
    )
    api_base: str = Field(
        default="",
        validation_alias=AliasChoices(
            "LANGCHAIN_OTEL_DEMO_API_BASE",
            "AGENTSEEK_API_BASE",
            "BUB_API_BASE",
        ),
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
    otlp_traces_endpoint: str = Field(
        default="http://127.0.0.1:4318/v1/traces",
        validation_alias=AliasChoices(
            "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT",
            "LANGCHAIN_OTEL_DEMO_OTLP_TRACES_ENDPOINT",
        ),
    )
    service_name: str = Field(
        default="langchain-otel-demo",
        validation_alias=AliasChoices(
            "OTEL_SERVICE_NAME",
            "LANGCHAIN_OTEL_DEMO_SERVICE_NAME",
        ),
    )

    def require_model(self) -> str:
        model = self.model.strip()
        if model:
            return model
        msg = "Set LANGCHAIN_OTEL_DEMO_MODEL (or AGENTSEEK_MODEL / BUB_MODEL) for the LangChain OTEL demo."
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


@lru_cache(maxsize=1)
def get_langchain_otel_sidecar_settings() -> LangChainOtelSidecarSettings:
    return LangChainOtelSidecarSettings()
