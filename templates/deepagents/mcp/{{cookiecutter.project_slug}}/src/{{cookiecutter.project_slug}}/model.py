"""Provider-aware chat model construction for the MCP agent."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

SUPPORTED_MODEL_PROVIDERS = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google_genai",
    "google_genai": "google_genai",
    "gemini": "google_genai",
}


@dataclass(frozen=True)
class ModelBinding:
    """One model instance and the exact DeepAgents profile key it resolves."""

    model: BaseChatModel
    provider: str
    model_name: str
    profile_key: str


def _environment_snapshot(environ: Mapping[str, str] | None = None) -> Mapping[str, str]:
    source = os.environ if environ is None else environ
    return MappingProxyType(dict(source))


def _nonempty_env(name: str, environ: Mapping[str, str]) -> str | None:
    value = environ.get(name)
    if value is None:
        return None
    return value.strip() or None


def normalize_provider(provider: str) -> str:
    """Normalize a supported provider alias to LangChain's provider name."""
    normalized = provider.strip().replace("-", "_").lower()
    try:
        return SUPPORTED_MODEL_PROVIDERS[normalized]
    except KeyError:
        supported = ", ".join(sorted({"anthropic", "google_genai", "openai"}))
        raise ValueError(
            f"Unsupported AGENTSEEK_MODEL_PROVIDER={provider!r}. Expected one of: {supported}."
        ) from None


def require_nonempty_model(environ: Mapping[str, str] | None = None) -> str:
    """Resolve the model name using AgentSeek's compatibility precedence."""
    snapshot = _environment_snapshot(environ)
    model_name = (
        _nonempty_env("AGENTSEEK_MODEL", snapshot)
        or _nonempty_env("DEEPAGENTS_MODEL", snapshot)
        or _nonempty_env("BUB_MODEL", snapshot)
        or "{{ cookiecutter.default_model }}".strip()
    )
    if not model_name:
        raise ValueError("Set AGENTSEEK_MODEL (or DEEPAGENTS_MODEL / BUB_MODEL) to a non-empty model name.")
    return model_name


def _split_prefixed_model(model_name: str) -> tuple[str | None, str]:
    if ":" not in model_name:
        return None, model_name
    provider_candidate, bare_model = model_name.split(":", maxsplit=1)
    try:
        provider = normalize_provider(provider_candidate)
    except ValueError:
        return None, model_name
    if not bare_model.strip():
        raise ValueError("The provider-prefixed model name must include a non-empty model after ':'.")
    return provider, bare_model.strip()


def _model_spec(environ: Mapping[str, str]) -> tuple[str, str]:
    raw_model = require_nonempty_model(environ)
    prefixed_provider, model_name = _split_prefixed_model(raw_model)
    if ":" in model_name:
        raise ValueError(
            "Resolved DeepAgents profile keys cannot contain more than one ':'; "
            "provider-native model identifiers containing ':' are unsupported."
        )
    configured_provider = _nonempty_env("AGENTSEEK_MODEL_PROVIDER", environ)
    if configured_provider is not None:
        provider = normalize_provider(configured_provider)
        if prefixed_provider is not None and prefixed_provider != provider:
            raise ValueError(
                "The model provider prefix does not match AGENTSEEK_MODEL_PROVIDER: "
                f"{raw_model!r} vs {configured_provider!r}."
            )
    else:
        provider = prefixed_provider or normalize_provider("{{ cookiecutter.default_model_provider }}")
    return provider, model_name


def provider_kwargs(provider: str, environ: Mapping[str, str] | None = None) -> dict[str, object]:
    """Return the shared credential and provider-native endpoint values."""
    snapshot = _environment_snapshot(environ)
    names = {
        "openai": ("OPENAI_API_KEY", "OPENAI_API_BASE"),
        "anthropic": ("ANTHROPIC_API_KEY", "ANTHROPIC_API_URL"),
        "google_genai": ("GOOGLE_API_KEY", "GOOGLE_API_BASE"),
    }
    key_name, base_name = names[provider]
    kwargs: dict[str, object] = {}
    if api_key := (
        _nonempty_env("AGENTSEEK_MODEL_API_KEY", snapshot)
        or _nonempty_env(key_name, snapshot)
    ):
        kwargs["api_key"] = api_key
    if base_url := _nonempty_env(base_name, snapshot):
        kwargs["base_url"] = base_url
    return kwargs


def model_profile_key() -> str:
    """Return the exact provider:model key resolved for DeepAgents profiles."""
    snapshot = _environment_snapshot()
    provider, model_name = _model_spec(snapshot)
    return f"{provider}:{model_name}"


def resolve_model_binding(environ: Mapping[str, str] | None = None) -> ModelBinding:
    """Build a model and exact profile key from one immutable environment snapshot."""
    snapshot = _environment_snapshot(environ)
    provider, model_name = _model_spec(snapshot)
    profile_key = f"{provider}:{model_name}"
    model = init_chat_model(
        model=model_name,
        model_provider=provider,
        **provider_kwargs(provider, snapshot),
    )
    return ModelBinding(
        model=model,
        provider=provider,
        model_name=model_name,
        profile_key=profile_key,
    )


def build_model() -> BaseChatModel:
    """Validate settings and construct a chat model from one environment snapshot."""
    return resolve_model_binding().model
