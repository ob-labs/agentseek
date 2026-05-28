from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping

from pydantic_settings import BaseSettings, SettingsConfigDict

AGENTSEEK_CTX_PREFIX = "AGENTSEEK_CTX_"

_ALIASES: tuple[str, ...] = (
    "STORAGE_BACKEND",
    "STORAGE_PATH",
    "STORAGE_URI_SCHEME",
    "STORAGE_COLD_BACKEND",
    "STORAGE_COLD_PATH",
    "OB_HOST",
    "OB_PORT",
    "OB_USER",
    "OB_PASSWORD",
    "OB_DB_NAME",
    "OB_TABLE_NAME",
    "EMBEDDING_PROVIDER",
    "EMBEDDING_CLASS_PATH",
    "EMBEDDING_MODEL",
    "EMBEDDING_DIMS",
    "EMBEDDING_BASE_URL",
    "LLM_PROVIDER",
    "LLM_CLASS_PATH",
    "LLM_MODEL",
    "LLM_BASE_URL",
    "SUMMARIZER_PROVIDER",
    "SUMMARIZER_L0_MAX_CHARS",
    "SUMMARIZER_L1_MAX_CHARS",
    "RETRIEVAL_DEFAULT_K",
    "RETRIEVAL_VECTOR_WEIGHT",
    "RETRIEVAL_FTS_WEIGHT",
    "RETRIEVAL_RERANKER_MODE",
    "EVOLUTION_ENABLED",
    "EVOLUTION_SEMANTIC_MERGE",
    "EVOLUTION_SEMANTIC_MERGE_THRESHOLD",
    "EVOLUTION_LLM_MERGE_ENABLED",
    "EVOLUTION_LLM_DISTILL_ENABLED",
    "OBSERVABILITY_AUDIT_ENABLED",
    "OBSERVABILITY_METRICS_ENABLED",
    "OBSERVABILITY_AUDIT_PATH",
    "GEO_ENABLED",
    "GEO_TABLE_NAME",
    "GEO_SRID",
    "LIFECYCLE_INTERVAL_SECONDS",
    "LIFECYCLE_AUTO_COMPACT",
    "DREAM_LLM_ENABLED",
    "SECURITY_ACL_ENABLED",
    "SECURITY_REDACT_SENSITIVE",
)


class ContextSeekAliasSettings(BaseSettings):
    """AGENTSEEK_CTX_* fallback values for ContextSeek flat env vars."""

    model_config = SettingsConfigDict(
        env_prefix=AGENTSEEK_CTX_PREFIX,
        case_sensitive=False,
        extra="ignore",
    )

    STORAGE_BACKEND: str | None = None
    STORAGE_PATH: str | None = None
    STORAGE_URI_SCHEME: str | None = None
    STORAGE_COLD_BACKEND: str | None = None
    STORAGE_COLD_PATH: str | None = None
    OB_HOST: str | None = None
    OB_PORT: str | None = None
    OB_USER: str | None = None
    OB_PASSWORD: str | None = None
    OB_DB_NAME: str | None = None
    OB_TABLE_NAME: str | None = None
    EMBEDDING_PROVIDER: str | None = None
    EMBEDDING_CLASS_PATH: str | None = None
    EMBEDDING_MODEL: str | None = None
    EMBEDDING_DIMS: str | None = None
    EMBEDDING_BASE_URL: str | None = None
    LLM_PROVIDER: str | None = None
    LLM_CLASS_PATH: str | None = None
    LLM_MODEL: str | None = None
    LLM_BASE_URL: str | None = None
    SUMMARIZER_PROVIDER: str | None = None
    SUMMARIZER_L0_MAX_CHARS: str | None = None
    SUMMARIZER_L1_MAX_CHARS: str | None = None
    RETRIEVAL_DEFAULT_K: str | None = None
    RETRIEVAL_VECTOR_WEIGHT: str | None = None
    RETRIEVAL_FTS_WEIGHT: str | None = None
    RETRIEVAL_RERANKER_MODE: str | None = None
    EVOLUTION_ENABLED: str | None = None
    EVOLUTION_SEMANTIC_MERGE: str | None = None
    EVOLUTION_SEMANTIC_MERGE_THRESHOLD: str | None = None
    EVOLUTION_LLM_MERGE_ENABLED: str | None = None
    EVOLUTION_LLM_DISTILL_ENABLED: str | None = None
    OBSERVABILITY_AUDIT_ENABLED: str | None = None
    OBSERVABILITY_METRICS_ENABLED: str | None = None
    OBSERVABILITY_AUDIT_PATH: str | None = None
    GEO_ENABLED: str | None = None
    GEO_TABLE_NAME: str | None = None
    GEO_SRID: str | None = None
    LIFECYCLE_INTERVAL_SECONDS: str | None = None
    LIFECYCLE_AUTO_COMPACT: str | None = None
    DREAM_LLM_ENABLED: str | None = None
    SECURITY_ACL_ENABLED: str | None = None
    SECURITY_REDACT_SENSITIVE: str | None = None


class ContextSeekPluginSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix=AGENTSEEK_CTX_PREFIX,
        case_sensitive=False,
        extra="ignore",
    )

    TENANT: str = "default"
    RETRIEVAL_DEFAULT_K: int = 5


def _settings_from_environ(environ: Mapping[str, str]) -> ContextSeekAliasSettings:
    payload: dict[str, str] = {}
    for key in _ALIASES:
        prefixed_key = f"{AGENTSEEK_CTX_PREFIX}{key}"
        value = environ.get(prefixed_key)
        if value is not None:
            payload[key] = value
    return ContextSeekAliasSettings.model_validate(payload)


def apply_contextseek_env_aliases(
    environ: MutableMapping[str, str] | None = None,
) -> None:
    """Let AGENTSEEK_CTX_* act as fallbacks for contextseek's flat env vars."""
    target = os.environ if environ is None else environ
    settings = ContextSeekAliasSettings() if environ is None else _settings_from_environ(target)
    for key, value in settings.model_dump(exclude_none=True).items():
        target.setdefault(key, str(value))
