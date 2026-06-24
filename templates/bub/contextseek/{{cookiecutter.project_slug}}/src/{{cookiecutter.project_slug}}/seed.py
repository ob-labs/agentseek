"""Idempotent seed script: pre-loads example entries into the ContextSeek store."""

from __future__ import annotations

_SEED_ENTRIES: list[dict[str, str]] = [
    {
        "content": (
            "ContextSeek turns runtime experience into reusable knowledge. "
            "It stores, retrieves, and evolves semantic memories so agents can "
            "recall past context across sessions without relying on long prompts."
        ),
        "scope": "contextseek",
        "source": "seed",
    },
    {
        "content": (
            "OceanBase is a financial-grade distributed relational database. "
            "It supports HTAP workloads, strong consistency, and multi-tenant "
            "isolation, and can serve as the persistent storage backend for "
            "ContextSeek when `AGENTSEEK_CTX_STORAGE_BACKEND=oceanbase`."
        ),
        "scope": "oceanbase",
        "source": "seed",
    },
    {
        "content": (
            "agentseek is a Bub-powered agent harness that exposes any Python "
            "function graph as an AG-UI compatible HTTP endpoint. It ships with "
            "a gateway, a CLI, and optional plugins such as agentseek-contextseek."
        ),
        "scope": "agentseek",
        "source": "seed",
    },
    {
        "content": (
            "The ctx HTTP API exposed by this project lets external tools feed "
            "knowledge into the running ContextSeek store without modifying the "
            "agent code. Use POST /ctx/add to ingest text, GET /ctx/retrieve to "
            "perform semantic search, and GET /ctx/overview to inspect all entries."
        ),
        "scope": "ctx-api",
        "source": "seed",
    },
]


def maybe_seed() -> None:
    """Pre-load seed entries if the store is empty (idempotent)."""
    try:
        from agentseek_contextseek.config import apply_contextseek_env_aliases
        from contextseek.client.contextseek import ContextSeek
    except ImportError as exc:
        raise RuntimeError(
            "contextseek and agentseek-contextseek are not installed. "
            "Run `uv sync` to install all dependencies."
        ) from exc

    from dotenv import load_dotenv

    load_dotenv()
    apply_contextseek_env_aliases()
    ctx = ContextSeek.from_settings()

    existing = ctx.retrieve("contextseek", scope="contextseek", k=1)
    if existing:
        return

    for entry in _SEED_ENTRIES:
        ctx.add(
            entry["content"],
            scope=entry["scope"],
            source=entry["source"],
        )

    print(f"Seeded {len(_SEED_ENTRIES)} example entries into ContextSeek store.")
