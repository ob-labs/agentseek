"""Sandbox provider selection for the DeepAgents coding agent."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

SUPPORTED_SANDBOX_PROVIDERS = {"daytona", "langsmith"}


def _nonempty_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def normalize_sandbox_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized in SUPPORTED_SANDBOX_PROVIDERS:
        return normalized
    supported = ", ".join(sorted(SUPPORTED_SANDBOX_PROVIDERS))
    raise ValueError(
        f"Unsupported AGENTSEEK_SANDBOX_PROVIDER={provider!r}. Expected one of: {supported}."
    )


def _best_effort_cleanup(action: Callable[[], None]) -> Callable[[], None]:
    def cleanup() -> None:
        try:
            action()
        except Exception:
            pass

    return cleanup


def create_sandbox_backend(provider: str | None = None) -> tuple[Any, Callable[[], None]]:
    selected = normalize_sandbox_provider(
        provider or os.getenv("AGENTSEEK_SANDBOX_PROVIDER") or "daytona"
    )
    if selected == "daytona":
        if not _nonempty_env("DAYTONA_API_KEY"):
            raise RuntimeError("DAYTONA_API_KEY is required when AGENTSEEK_SANDBOX_PROVIDER=daytona.")
        from daytona import Daytona
        from langchain_daytona import DaytonaSandbox

        client = Daytona()
        sandbox = client.create()
        cleanup = _best_effort_cleanup(lambda: client.delete(sandbox))
        try:
            backend = DaytonaSandbox(sandbox=sandbox)
        except Exception:
            cleanup()
            raise
        return backend, cleanup

    if not _nonempty_env("LANGSMITH_API_KEY"):
        raise RuntimeError("LANGSMITH_API_KEY is required when AGENTSEEK_SANDBOX_PROVIDER=langsmith.")
    from deepagents.backends import LangSmithSandbox
    from langsmith.sandbox import SandboxClient

    client = SandboxClient()
    sandbox = client.create_sandbox()
    cleanup = _best_effort_cleanup(lambda: client.delete_sandbox(sandbox.name))
    try:
        backend = LangSmithSandbox(sandbox=sandbox)
    except Exception:
        cleanup()
        raise
    return backend, cleanup
