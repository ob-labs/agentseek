"""DeepAgents content builder graph, served by ``langgraph dev``.

This module wires up a ``create_deep_agent`` with brand-voice memory
(``AGENTS.md``), content skills (``skills/``), a researcher subagent
(``subagents.yaml``), and image generation tools — mirroring the upstream
``langchain-ai/deepagents/examples/content-builder-agent/content_writer.py``
with provider-first runtime config so the generated app can target OpenAI,
Anthropic, or Gemini from the same ``.env``.
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path

import yaml
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from {{ cookiecutter.project_slug }}.tools import (
    generate_cover,
    generate_social_image,
    web_search,
)

load_dotenv()

EXAMPLE_DIR = Path(__file__).resolve().parents[2]

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


def _normalize_provider(provider: str) -> str:
    normalized = provider.strip().replace("-", "_").lower()
    if normalized in SUPPORTED_MODEL_PROVIDERS:
        return SUPPORTED_MODEL_PROVIDERS[normalized]
    supported = ", ".join(sorted({"openai", "anthropic", "google_genai"}))
    raise ValueError(
        f"Unsupported AGENTSEEK_MODEL_PROVIDER={provider!r}. "
        f"Expected one of: {supported}."
    )


def _split_prefixed_model(model_name: str) -> tuple[str | None, str]:
    if ":" not in model_name:
        return None, model_name
    provider_candidate, bare_model = model_name.split(":", maxsplit=1)
    try:
        normalized_provider = _normalize_provider(provider_candidate)
    except ValueError:
        return None, model_name
    return normalized_provider, bare_model


DEFAULT_MODEL_RAW = (
    _nonempty_env("AGENTSEEK_MODEL")
    or _nonempty_env("DEEPAGENTS_MODEL")
    or _nonempty_env("BUB_MODEL")
    or "{{ cookiecutter.default_model }}".strip()
    or None
)
if not DEFAULT_MODEL_RAW:
    raise ValueError(
        "No model configured. Set AGENTSEEK_MODEL in .env "
        "(e.g. AGENTSEEK_MODEL=gpt-4.1-mini)."
    )
DEFAULT_MODEL_PROVIDER_RAW = os.getenv("AGENTSEEK_MODEL_PROVIDER")
DEFAULT_MODEL_PROVIDER_DEFAULT = "{{ cookiecutter.default_model_provider }}"

prefixed_model_provider, DEFAULT_MODEL = _split_prefixed_model(DEFAULT_MODEL_RAW)
if DEFAULT_MODEL_PROVIDER_RAW:
    MODEL_PROVIDER = _normalize_provider(DEFAULT_MODEL_PROVIDER_RAW)
    if prefixed_model_provider and prefixed_model_provider != MODEL_PROVIDER:
        raise ValueError(
            "AGENTSEEK_MODEL provider prefix does not match AGENTSEEK_MODEL_PROVIDER: "
            f"{DEFAULT_MODEL_RAW!r} vs {DEFAULT_MODEL_PROVIDER_RAW!r}."
        )
else:
    MODEL_PROVIDER = prefixed_model_provider or _normalize_provider(DEFAULT_MODEL_PROVIDER_DEFAULT)

_stream_chunk_timeout_env = os.getenv("LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S")
STREAM_CHUNK_TIMEOUT_S: float | None = 300.0
if _stream_chunk_timeout_env not in (None, ""):
    try:
        _parsed_timeout = float(_stream_chunk_timeout_env)
    except ValueError:
        warnings.warn(
            "Ignoring invalid LANGCHAIN_OPENAI_STREAM_CHUNK_TIMEOUT_S value; "
            "using the default 300s timeout instead.",
            stacklevel=2,
        )
    else:
        STREAM_CHUNK_TIMEOUT_S = None if _parsed_timeout <= 0 else _parsed_timeout


SUBAGENT_MODEL_RAW = (
    os.getenv("AGENTSEEK_SUBAGENT_MODEL")
    or os.getenv("DEEPAGENTS_SUBAGENT_MODEL")
    or None
)

# --- Provider kwargs shared by main model and subagents --------------------
# Both use the same provider, API key, and base URL. Only the model name
# differs between them.

PROVIDER_KWARGS: dict[str, object] = {
    "model_provider": MODEL_PROVIDER,
}
if MODEL_PROVIDER == "openai":
    if _nonempty_env("OPENAI_API_KEY"):
        PROVIDER_KWARGS["api_key"] = _nonempty_env("OPENAI_API_KEY")
    if _nonempty_env("OPENAI_API_BASE"):
        PROVIDER_KWARGS["base_url"] = _nonempty_env("OPENAI_API_BASE")
    PROVIDER_KWARGS["stream_chunk_timeout"] = STREAM_CHUNK_TIMEOUT_S
elif MODEL_PROVIDER == "anthropic":
    if _nonempty_env("ANTHROPIC_API_KEY"):
        PROVIDER_KWARGS["api_key"] = _nonempty_env("ANTHROPIC_API_KEY")
    if _nonempty_env("ANTHROPIC_API_URL"):
        PROVIDER_KWARGS["base_url"] = _nonempty_env("ANTHROPIC_API_URL")
elif MODEL_PROVIDER == "google_genai":
    if _nonempty_env("GOOGLE_API_KEY"):
        PROVIDER_KWARGS["api_key"] = _nonempty_env("GOOGLE_API_KEY")
    if _nonempty_env("GOOGLE_API_BASE"):
        PROVIDER_KWARGS["base_url"] = _nonempty_env("GOOGLE_API_BASE")

model = init_chat_model(model=DEFAULT_MODEL, **PROVIDER_KWARGS)


def _make_subagent_model(model_name: str) -> object:
    """Create a subagent LLM sharing the main provider + base URL."""
    _, bare_model = _split_prefixed_model(model_name)
    return init_chat_model(model=bare_model, **PROVIDER_KWARGS)


def _load_subagents(config_path: Path) -> list[dict]:
    """Load subagent definitions from YAML and wire up tools.

    Subagents share the same provider and base URL as the main model.
    The subagent model name can be overridden globally via
    ``AGENTSEEK_SUBAGENT_MODEL`` (or ``DEEPAGENTS_SUBAGENT_MODEL``) env var;
    when set, it takes precedence over the per-subagent ``model`` in YAML.
    """
    available_tools = {
        "web_search": web_search,
    }

    with open(config_path) as f:
        config = yaml.safe_load(f)

    subagents = []
    for name, spec in config.items():
        subagent: dict = {
            "name": name,
            "description": spec["description"],
            "system_prompt": spec["system_prompt"],
        }
        model_name = SUBAGENT_MODEL_RAW or spec.get("model")
        if model_name:
            subagent["model"] = _make_subagent_model(model_name)
        if "tools" in spec:
            subagent["tools"] = [available_tools[t] for t in spec["tools"]]
        subagents.append(subagent)

    return subagents


graph = create_deep_agent(
    model=model,
    memory=["./AGENTS.md"],
    skills=["./skills/"],
    tools=[generate_cover, generate_social_image],
    subagents=_load_subagents(EXAMPLE_DIR / "subagents.yaml"),
    backend=FilesystemBackend(root_dir=EXAMPLE_DIR, virtual_mode=False),
)
