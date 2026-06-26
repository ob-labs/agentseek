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

from pydantic import AliasChoices, Field
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

    When contextseek's LLM is enabled (``AGENTSEEK_CTX_LLM_PROVIDER`` is not
    ``none``, or ``AGENTSEEK_CTX_LLM_MODEL`` is set), the Bub runtime
    credentials are bridged to the LangChain env vars used by contextseek:

    - ``BUB_API_KEY`` / ``BUB_OPENAI_API_KEY``   → provider key (fallback only)
    - ``BUB_API_BASE`` / ``BUB_OPENAI_API_BASE`` → provider base URL (fallback only)

    This lets contextseek's internal LLM reuse the same API endpoint as the
    Bub agent without duplicating credentials in ``.env``. Legacy
    ``AGENTSEEK_*`` credentials are still accepted as lower-priority fallbacks.
    """
    target = os.environ if environ is None else environ
    _apply_contextseek_prefixed_aliases(target)
    _maybe_bridge_llm_credentials(target)


# Maps a provider name → (api_key_var, base_url_var | None).
# base_url_var is only applied for providers that accept a custom base URL.
_PROVIDER_CREDS: dict[str, tuple[str, str | None]] = {
    "openai": ("OPENAI_API_KEY", "OPENAI_BASE_URL"),
    "anthropic": ("ANTHROPIC_API_KEY", None),
    "google": ("GOOGLE_API_KEY", None),
    "cohere": ("COHERE_API_KEY", None),
    "mistral": ("MISTRAL_API_KEY", None),
    "dashscope": ("DASHSCOPE_API_KEY", None),
    "tongyi": ("DASHSCOPE_API_KEY", None),
    "deepseek": ("DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL"),
}

# Maps a provider name → LangChain chat class path.
_PROVIDER_CLASS_PATH: dict[str, str] = {
    "openai": "langchain_openai.ChatOpenAI",
    "anthropic": "langchain_anthropic.ChatAnthropic",
    "google": "langchain_google_genai.ChatGoogleGenerativeAI",
    "cohere": "langchain_cohere.ChatCohere",
    "mistral": "langchain_mistralai.ChatMistralAI",
    "dashscope": "langchain_community.chat_models.ChatTongyi",
    "tongyi": "langchain_community.chat_models.ChatTongyi",
    "deepseek": "langchain_openai.ChatOpenAI",
}

# Fragments of LangChain class paths → provider name (for reverse lookup).
_CLASS_PATH_PROVIDER: dict[str, str] = {
    "langchain_openai": "openai",
    "langchain_anthropic": "anthropic",
    "langchain_google_genai": "google",
    "langchain_google_vertexai": "google",
    "langchain_cohere": "cohere",
    "langchain_mistralai": "mistral",
    "chattongyi": "dashscope",
    "tongyi": "dashscope",
    "deepseek": "deepseek",
}


class RuntimeBridgeSettings(BaseSettings):
    """Runtime model credentials shared with ContextSeek's LangChain bridge."""

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=True)

    model: str = Field(
        default="",
        validation_alias=AliasChoices("BUB_MODEL", "AGENTSEEK_MODEL"),
    )
    api_key: str = Field(
        default="",
        validation_alias=AliasChoices("BUB_API_KEY", "BUB_OPENAI_API_KEY", "AGENTSEEK_API_KEY"),
    )
    api_base: str = Field(
        default="",
        validation_alias=AliasChoices("BUB_API_BASE", "BUB_OPENAI_API_BASE", "AGENTSEEK_API_BASE"),
    )
    ctx_llm_provider: str = Field(default="none", validation_alias=AliasChoices(f"{AGENTSEEK_CTX_PREFIX}LLM_PROVIDER"))
    ctx_llm_model: str = Field(default="", validation_alias=AliasChoices(f"{AGENTSEEK_CTX_PREFIX}LLM_MODEL"))
    ctx_llm_class_path: str = Field(
        default="",
        validation_alias=AliasChoices(f"{AGENTSEEK_CTX_PREFIX}LLM_CLASS_PATH"),
    )

    @property
    def llm_enabled(self) -> bool:
        return self.ctx_llm_provider.lower() != "none" or bool(self.ctx_llm_model)

    @property
    def provider(self) -> str:
        class_path = self.ctx_llm_class_path.lower()
        if class_path:
            for fragment, provider in _CLASS_PATH_PROVIDER.items():
                if fragment in class_path:
                    return provider

        if ":" in self.model:
            prefix = self.model.split(":", 1)[0].lower()
            if prefix in _PROVIDER_CREDS:
                return prefix

        return "openai"

    @property
    def unprefixed_model(self) -> str:
        if ":" not in self.model:
            return ""
        return self.model.split(":", 1)[1]


def _maybe_bridge_llm_credentials(target: MutableMapping[str, str]) -> None:
    """Bridge Bub credentials to provider-specific LangChain vars when ctx LLM is enabled.

    Only runs when contextseek LLM is enabled (``AGENTSEEK_CTX_LLM_PROVIDER``
    != ``none`` or ``AGENTSEEK_CTX_LLM_MODEL`` is set).

    Derives the following from ``BUB_MODEL`` / ``BUB_API_KEY`` /
    ``BUB_API_BASE`` (all as ``setdefault`` — explicit values always win):

    - Provider-specific API key  (e.g. ``OPENAI_API_KEY``)
    - Provider-specific base URL (e.g. ``OPENAI_BASE_URL``)
    - ``LLM_CLASS_PATH``         (e.g. ``langchain_openai.ChatOpenAI``)
    - ``LLM_MODEL``              (model name stripped of provider prefix)
    """
    settings = RuntimeBridgeSettings.model_validate(dict(target))
    if not settings.llm_enabled:
        return

    provider = settings.provider

    key_var, base_var = _PROVIDER_CREDS.get(provider, ("OPENAI_API_KEY", "OPENAI_BASE_URL"))
    if settings.api_key:
        target.setdefault(key_var, settings.api_key)
    if settings.api_base and base_var:
        target.setdefault(base_var, settings.api_base)

    # --- LLM_CLASS_PATH: auto-set from provider if not explicitly configured ---
    ctx_class_path_key = f"{AGENTSEEK_CTX_PREFIX}LLM_CLASS_PATH"
    if not target.get(ctx_class_path_key):
        class_path = _PROVIDER_CLASS_PATH.get(provider)
        if class_path:
            target[ctx_class_path_key] = class_path

    # --- LLM_MODEL: strip provider prefix from BUB_MODEL if not set ---
    ctx_model_key = f"{AGENTSEEK_CTX_PREFIX}LLM_MODEL"
    if not target.get(ctx_model_key) and settings.unprefixed_model:
        target[ctx_model_key] = settings.unprefixed_model


def _apply_contextseek_prefixed_aliases(target: MutableMapping[str, str]) -> None:
    """Apply ``AGENTSEEK_CTX_*`` fallbacks for upstream contextseek env vars."""
    for env_var in _upstream_env_vars():
        alias = f"{AGENTSEEK_CTX_PREFIX}{env_var}"
        if alias in target:
            target.setdefault(env_var, target[alias])


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
