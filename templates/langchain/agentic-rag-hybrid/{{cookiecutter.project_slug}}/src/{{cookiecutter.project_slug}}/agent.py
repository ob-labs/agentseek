from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any, Literal

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool

from .hybrid import clamp_top_k, normalize_query, normalize_search_mode
from .middleware import hybrid_mode_guidance
from .models import SearchTrace
from .observability import configure_tracing
from .settings import Settings, get_settings
from .store import HybridImageStore

load_dotenv()

SYSTEM_PROMPT = "{{ cookiecutter.system_prompt }}"

SUPPORTED_MODEL_PROVIDERS = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google_genai",
    "google_genai": "google_genai",
    "gemini": "google_genai",
}


def _nonempty_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _openai_compatible_base_url() -> str:
    return _nonempty_env("AGENTSEEK_API_BASE") or _nonempty_env("OPENAI_API_BASE") or "https://api.siliconflow.cn/v1"


def _openai_compatible_api_key() -> str | None:
    base_url = _openai_compatible_base_url().lower()
    if "siliconflow" in base_url:
        return _nonempty_env("AGENTSEEK_API_KEY") or _nonempty_env("SILICONFLOW_API_KEY") or _nonempty_env("OPENAI_API_KEY")
    return _nonempty_env("AGENTSEEK_API_KEY") or _nonempty_env("OPENAI_API_KEY") or _nonempty_env("SILICONFLOW_API_KEY")


def _native_provider_api_key(name: str) -> str | None:
    return _nonempty_env(name) or _nonempty_env("AGENTSEEK_API_KEY")


def _normalize_provider(provider: str) -> str:
    normalized = provider.strip().replace("-", "_").lower()
    if normalized in SUPPORTED_MODEL_PROVIDERS:
        return SUPPORTED_MODEL_PROVIDERS[normalized]
    supported = ", ".join(sorted({"openai", "anthropic", "google_genai"}))
    raise ValueError(f"Unsupported AGENTSEEK_MODEL_PROVIDER={provider!r}. Expected one of: {supported}.")


def _split_prefixed_model(model_name: str) -> tuple[str | None, str]:
    if ":" not in model_name:
        return None, model_name
    provider_candidate, bare_model = model_name.split(":", maxsplit=1)
    try:
        normalized_provider = _normalize_provider(provider_candidate)
    except ValueError:
        return None, model_name
    return normalized_provider, bare_model


DEFAULT_MODEL_RAW = os.getenv("AGENTSEEK_MODEL") or os.getenv("BUB_MODEL") or "{{ cookiecutter.default_model }}"
DEFAULT_MODEL_PROVIDER_RAW = os.getenv("AGENTSEEK_MODEL_PROVIDER")
DEFAULT_MODEL_PROVIDER_DEFAULT = "{{ cookiecutter.default_model_provider }}"

prefixed_model_provider, DEFAULT_MODEL = _split_prefixed_model(DEFAULT_MODEL_RAW)
if DEFAULT_MODEL_PROVIDER_RAW:
    MODEL_PROVIDER = _normalize_provider(DEFAULT_MODEL_PROVIDER_RAW)
    if prefixed_model_provider and prefixed_model_provider != MODEL_PROVIDER:
        raise ValueError("AGENTSEEK_MODEL provider prefix does not match AGENTSEEK_MODEL_PROVIDER.")
else:
    MODEL_PROVIDER = prefixed_model_provider or _normalize_provider(DEFAULT_MODEL_PROVIDER_DEFAULT)

def _serialize_trace(trace: SearchTrace) -> tuple[str, dict[str, Any]]:
    lines = [
        f"Hybrid search mode: {trace.mode}",
        f"Query: {trace.query}",
        trace.explanation,
        "",
    ]
    for hit in trace.hits:
        lines.append(f"{hit.rank}. {hit.file_name}: {hit.caption}")
    return "\n".join(lines), asdict(trace)


def _prepare_search_request(query: str, top_k: int, settings: Settings) -> tuple[str, int]:
    return normalize_query(query), clamp_top_k(top_k, settings.hybrid_max_top_k)


@tool(response_format="content_and_artifact")
def hybrid_search_knowledge_base(
    query: str,
    top_k: int = 5,
    search_mode: Literal["balanced", "semantic", "keyword", "exact"] = "balanced",
):
    """Search the indexed image knowledge base with hybrid vector, sparse, and full-text retrieval.

    Use semantic for visual/conceptual similarity, keyword for term-heavy queries,
    exact for filenames/labels/exact categories, and balanced for mixed intent.
    """
    settings = get_settings()
    query, top_k = _prepare_search_request(query, top_k, settings)
    mode = normalize_search_mode(search_mode)
    trace = HybridImageStore(settings=settings).search_text(query=query, mode=mode, top_k=top_k)
    return _serialize_trace(trace)


MODEL_INIT_KWARGS: dict[str, object] = {
    "model": DEFAULT_MODEL,
    "model_provider": MODEL_PROVIDER,
}
if MODEL_PROVIDER == "openai":
    if api_key := _openai_compatible_api_key():
        MODEL_INIT_KWARGS["api_key"] = api_key
    MODEL_INIT_KWARGS["base_url"] = _openai_compatible_base_url()
elif MODEL_PROVIDER == "anthropic":
    if _nonempty_env("AGENTSEEK_API_KEY") or _nonempty_env("ANTHROPIC_API_KEY"):
        MODEL_INIT_KWARGS["api_key"] = _native_provider_api_key("ANTHROPIC_API_KEY")
    if _nonempty_env("ANTHROPIC_API_URL"):
        MODEL_INIT_KWARGS["base_url"] = _nonempty_env("ANTHROPIC_API_URL")
elif MODEL_PROVIDER == "google_genai":
    if _nonempty_env("AGENTSEEK_API_KEY") or _nonempty_env("GOOGLE_API_KEY"):
        MODEL_INIT_KWARGS["api_key"] = _native_provider_api_key("GOOGLE_API_KEY")
    if _nonempty_env("GOOGLE_API_BASE"):
        MODEL_INIT_KWARGS["base_url"] = _nonempty_env("GOOGLE_API_BASE")

configure_tracing(get_settings())
model = init_chat_model(**MODEL_INIT_KWARGS)

graph = create_agent(
    model=model,
    tools=[hybrid_search_knowledge_base],
    system_prompt=SYSTEM_PROMPT,
    middleware=[hybrid_mode_guidance],
)
