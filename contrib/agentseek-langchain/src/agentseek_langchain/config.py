from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class LangChainSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_prefix="BUB_LANGCHAIN_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Uppercase field name so the env var is `BUB_LANGCHAIN_SPEC` (not `BUB_LANGCHAIN_spec`).
    SPEC: str = ""


@lru_cache(maxsize=1)
def get_langchain_settings() -> LangChainSettings:
    return LangChainSettings()
