"""ctx HTTP server — mounts the full contextseek HTTP API under /ctx.

Available routes (provided by contextseek.http.server):
  POST /ctx/add              ingest a new context item
  POST /ctx/retrieve         semantic search
  POST /ctx/expand           fetch L0 full text by item ids
  POST /ctx/forget           soft-delete an item
  POST /ctx/delete           hard-delete an item
  POST /ctx/feedback         apply relevance feedback
  POST /ctx/compact          run evolution compaction
  POST /ctx/dream            trigger background dream cycle
  POST /ctx/upstream         walk derivation links
  POST /ctx/evidence_chain   compute full evidence chain DAG
  POST /ctx/chain_confidence quick propagated confidence lookup
  POST /ctx/items            list items in a scope
  GET  /ctx/overview         scope evolution stats
  GET  /ctx/metrics          observability metrics
  GET  /ctx/health           health check
  GET  /ctx/docs             interactive API docs (Swagger UI)
"""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI

app = FastAPI(title="{{ cookiecutter.project_name }}", version="0.1.0")

_ctx_mounted = False


def _mount_ctx() -> None:
    global _ctx_mounted  # noqa: PLW0603
    if _ctx_mounted:
        return
    _ctx_mounted = True

    try:
        from agentseek_contextseek.config import apply_contextseek_env_aliases
        from contextseek.client.contextseek import ContextSeek
        from contextseek.http.server import create_app as cs_create_app
    except ImportError as exc:
        raise RuntimeError(
            "contextseek[http] and agentseek-contextseek are required. "
            "Run `uv sync`."
        ) from exc

    from dotenv import load_dotenv

    load_dotenv()
    apply_contextseek_env_aliases()
    ctx = ContextSeek.from_settings()
    app.mount("/ctx", cs_create_app(client=ctx))


_mount_ctx()


def main() -> None:
    port = int(os.environ.get("CTX_SERVER_PORT", "{{ cookiecutter.ctx_server_port }}"))
    uvicorn.run("{{ cookiecutter.project_slug }}.server:app", host="127.0.0.1", port=port, reload=False)
