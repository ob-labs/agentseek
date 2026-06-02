"""``agentseek-contextseek`` configuration glue.

This module does **not** mirror contextseek's settings model. Instead, it
*reflects* the upstream ``ContextSeekSettings`` class at runtime to discover
which env vars contextseek actually consumes, and then lets
``AGENTSEEK_CTX_<NAME>`` act as a fallback for each one.

Why reflection: contextseek owns the canonical list of knobs. Hard-coding a
copy here drifts the moment upstream adds, renames, or removes a setting
(it had already happened by the time of this refactor — the old copy was
missing dream/security/lifecycle fields and had ``GEO_TABLE_NAME`` mis-spelled
where the real var is ``GEO_GEO_TABLE_NAME``).
"""

from __future__ import annotations

import os
from collections.abc import Iterator, MutableMapping
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

AGENTSEEK_CTX_PREFIX = "AGENTSEEK_CTX_"


class ContextSeekPluginSettings(BaseSettings):
    """Settings owned by the agentseek plugin itself (not contextseek)."""

    model_config = SettingsConfigDict(
        env_prefix=AGENTSEEK_CTX_PREFIX,
        case_sensitive=False,
        extra="ignore",
    )

    TENANT: str = "default"
    RETRIEVAL_DEFAULT_K: int = 5


def apply_contextseek_env_aliases(
    environ: MutableMapping[str, str] | None = None,
) -> None:
    """Let ``AGENTSEEK_CTX_*`` act as fallbacks for contextseek's flat env vars.

    If contextseek is not importable, this is a no-op so that starting
    agentseek without the optional dependency does not raise.
    """
    target = os.environ if environ is None else environ
    for env_var in _upstream_env_vars():
        aliased = target.get(f"{AGENTSEEK_CTX_PREFIX}{env_var}")
        if aliased is not None:
            target.setdefault(env_var, aliased)


@lru_cache(maxsize=1)
def _upstream_env_vars() -> tuple[str, ...]:
    """Names of every env var ``ContextSeekSettings`` reads, reflected once."""
    try:
        from contextseek.config import ContextSeekSettings
    except ModuleNotFoundError:
        return ()
    return tuple(_iter_env_vars(ContextSeekSettings))


def _iter_env_vars(settings_cls: type[BaseSettings]) -> Iterator[str]:
    """Yield ``PREFIX + FIELD_NAME`` for every nested BaseSettings group.

    Mirrors pydantic-settings' own ``env_prefix`` + uppercase resolution; the
    upstream ``ContextSeekSettings`` is a flat collection of nested settings
    groups (storage, ob, embedding, …), each with its own ``env_prefix``.
    """
    case_sensitive = settings_cls.model_config.get("case_sensitive", False)
    for field_info in settings_cls.model_fields.values():
        group_cls = field_info.annotation
        if not isinstance(group_cls, type) or not issubclass(group_cls, BaseSettings):
            continue
        prefix = group_cls.model_config.get("env_prefix", "")
        for sub_name in group_cls.model_fields:
            env_name = f"{prefix}{sub_name}"
            yield env_name if case_sensitive else env_name.upper()
