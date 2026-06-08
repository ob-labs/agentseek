"""DeepAgents sandbox coding agent, served by `langgraph dev`.

Uses a LangSmith sandbox backend so the agent can execute shell commands
and interact with an isolated filesystem. The model provider abstraction
mirrors the research template: set AGENTSEEK_MODEL_PROVIDER + AGENTSEEK_MODEL
in .env to target OpenAI, Anthropic, or Gemini.
"""

from __future__ import annotations

import atexit
import os
import warnings

from deepagents import create_deep_agent
from deepagents.backends import LangSmithSandbox
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langsmith.sandbox import SandboxClient

from {{ cookiecutter.project_slug }}.prompts import SYSTEM_PROMPT

load_dotenv()

# ---------------------------------------------------------------------------
# Model provider resolution (same pattern as deepagents/research template)
# ---------------------------------------------------------------------------

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
    os.getenv("AGENTSEEK_MODEL")
    or os.getenv("DEEPAGENTS_MODEL")
    or os.getenv("BUB_MODEL")
    or "{{ cookiecutter.default_model }}"
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

# ---------------------------------------------------------------------------
# Model init
# ---------------------------------------------------------------------------

MODEL_INIT_KWARGS: dict[str, object] = {
    "model": DEFAULT_MODEL,
    "model_provider": MODEL_PROVIDER,
}
if MODEL_PROVIDER == "openai":
    if _nonempty_env("OPENAI_API_KEY"):
        MODEL_INIT_KWARGS["api_key"] = _nonempty_env("OPENAI_API_KEY")
    if _nonempty_env("OPENAI_API_BASE"):
        MODEL_INIT_KWARGS["base_url"] = _nonempty_env("OPENAI_API_BASE")
    MODEL_INIT_KWARGS["stream_chunk_timeout"] = STREAM_CHUNK_TIMEOUT_S
elif MODEL_PROVIDER == "anthropic":
    if _nonempty_env("ANTHROPIC_API_KEY"):
        MODEL_INIT_KWARGS["api_key"] = _nonempty_env("ANTHROPIC_API_KEY")
    if _nonempty_env("ANTHROPIC_API_URL"):
        MODEL_INIT_KWARGS["base_url"] = _nonempty_env("ANTHROPIC_API_URL")
elif MODEL_PROVIDER == "google_genai":
    if _nonempty_env("GOOGLE_API_KEY"):
        MODEL_INIT_KWARGS["api_key"] = _nonempty_env("GOOGLE_API_KEY")
    if _nonempty_env("GOOGLE_API_BASE"):
        MODEL_INIT_KWARGS["base_url"] = _nonempty_env("GOOGLE_API_BASE")

model = init_chat_model(**MODEL_INIT_KWARGS)

# ---------------------------------------------------------------------------
# Sandbox backend + lifecycle cleanup
#
# The sandbox is created once per process. On hot-reload (langgraph dev),
# the previous module's atexit handler deletes its sandbox before the new
# module creates a fresh one, so sandboxes don't leak.
# ---------------------------------------------------------------------------

_sandbox_client = SandboxClient()
_ls_sandbox = _sandbox_client.create_sandbox()
backend = LangSmithSandbox(sandbox=_ls_sandbox)


def _cleanup_sandbox() -> None:
    try:
        _sandbox_client.delete_sandbox(_ls_sandbox.name)
    except Exception:
        pass


atexit.register(_cleanup_sandbox)

# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------

graph = create_deep_agent(
    model=model,
    system_prompt=SYSTEM_PROMPT,
    backend=backend,
)
