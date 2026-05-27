from __future__ import annotations

import os

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


def apply_contextseek_env_aliases(
    environ: dict[str, str] | None = None,
) -> None:
    """Let AGENTSEEK_CTX_* act as fallbacks for contextseek's flat env vars."""
    target = os.environ if environ is None else environ
    for key in _ALIASES:
        alias = f"{AGENTSEEK_CTX_PREFIX}{key}"
        value = target.get(alias)
        if value is not None:
            target.setdefault(key, value)
