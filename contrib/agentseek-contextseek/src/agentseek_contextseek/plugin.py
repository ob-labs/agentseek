from __future__ import annotations

import asyncio
import importlib
import os
from typing import Any

from bub import hookimpl
from bub.types import State
from loguru import logger

from agentseek_contextseek.config import apply_contextseek_env_aliases


class ContextSeekPlugin:
    """Bub plugin: wires the contextseek semantic layer into the agentseek hook pipeline."""

    def __init__(self) -> None:
        self._client = None
        self._client_initialized = False
        apply_contextseek_env_aliases()

    def _get_client(self):
        if self._client_initialized:
            return self._client
        self._client_initialized = True
        try:
            cs = importlib.import_module("contextseek.client.contextseek")
            self._client = cs.ContextSeek.from_settings()
            logger.info("ContextSeek client initialized.")
        except Exception as exc:
            logger.warning(f"ContextSeek client init failed, semantic context disabled: {exc}")
        return self._client

    def _scope_from_state(self, state: State) -> str:
        tenant = os.environ.get("AGENTSEEK_CTX_TENANT", "default")
        chat_id = state.get("chat_id", "local")
        session_id = state.get("session_id") or "default"
        return f"{tenant}/{chat_id}/{session_id}"

    @hookimpl(trylast=True)
    async def before_model(
        self,
        prompt: str | list[dict[str, Any]],
        session_id: str,
        state: State,
    ) -> str | list[dict[str, Any]] | None:
        """Retrieve semantic context and inject it into the system prompt."""
        client = self._get_client()
        if client is None:
            return None

        query = prompt if isinstance(prompt, str) else _extract_text(prompt)
        if not query:
            return None

        scope = self._scope_from_state(state)
        try:
            hits = await asyncio.to_thread(client.retrieve, query, scope=scope, k=5)
        except Exception as exc:
            logger.debug(f"ContextSeek retrieve skipped: {exc}")
            return None

        if not hits:
            return None

        context_block = _format_context_block(hits)
        return _inject_context(prompt, context_block)

    @hookimpl
    async def after_model(
        self,
        prompt: str | list[dict[str, Any]],
        response: str,
        session_id: str,
        state: State,
    ) -> None:
        """Write model output into the contextseek evolution pipeline."""
        client = self._get_client()
        if client is None or not response:
            return

        scope = self._scope_from_state(state)
        try:
            await asyncio.to_thread(
                client.add,
                response,
                scope=scope,
                source=f"agentseek://session/{session_id}",
                tags=["agent-response", "execution-trace"],
            )
        except Exception as exc:
            logger.debug(f"ContextSeek add skipped: {exc}")


def _extract_text(messages: list[dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m.get("role") == "user":
            content = m.get("content", "")
            return content if isinstance(content, str) else ""
    return ""


def _format_context_block(hits: Any) -> str:
    lines = ["[ContextSeek]"]
    for h in hits:
        lines.append(f"- [{h.item.stage.value}] {h.item.summary or h.item.content_text[:120]}")
    return "\n".join(lines)


def _inject_context(
    prompt: str | list[dict[str, Any]],
    context_block: str,
) -> str | list[dict[str, Any]]:
    if isinstance(prompt, str):
        return f"{context_block}\n\n{prompt}"
    result = list(prompt)
    for i, m in enumerate(result):
        if m.get("role") == "system":
            existing = m.get("content", "")
            result[i] = {**m, "content": f"{existing}\n\n{context_block}"}
            return result
    return [{"role": "system", "content": context_block}, *result]
