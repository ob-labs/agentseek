from __future__ import annotations

import asyncio
import importlib
from typing import Any

from bub import hookimpl
from bub.envelope import content_of, field_of
from bub.types import Envelope, State
from loguru import logger

from agentseek_contextseek.config import ContextSeekPluginSettings, apply_contextseek_env_aliases


class ContextSeekPlugin:
    """Bub plugin: wires the contextseek semantic layer into the agentseek hook pipeline."""

    def __init__(self, framework: object | None = None) -> None:
        del framework
        self._client = None
        self._client_initialized = False
        apply_contextseek_env_aliases()
        self._settings = ContextSeekPluginSettings()

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

    def _scope_from_message(self, message: Envelope, session_id: str) -> str:
        tenant = self._settings.TENANT
        chat_id = field_of(message, "chat_id", "local")
        return f"{tenant}/{chat_id}/{session_id}"

    @hookimpl
    async def load_state(
        self,
        message: Envelope,
        session_id: str,
    ) -> State:
        """Retrieve semantic context and store it for prompt assembly."""
        client = self._get_client()
        if client is None:
            return {}

        query = content_of(message).strip()
        if not query:
            return {}

        scope = self._scope_from_message(message, session_id)
        try:
            hits = await asyncio.to_thread(client.retrieve, query, scope=scope, k=self._settings.RETRIEVAL_DEFAULT_K)
        except Exception as exc:
            logger.debug(f"ContextSeek retrieve skipped: {exc}")
            return {"_contextseek_scope": scope}

        if not hits:
            return {"_contextseek_scope": scope}

        return {
            "_contextseek_scope": scope,
            "_contextseek_block": _format_context_block(hits),
        }

    @hookimpl
    async def build_prompt(
        self,
        message: Envelope,
        session_id: str,
        state: State,
    ) -> str | None:
        del session_id
        context_block = state.get("_contextseek_block")
        if not isinstance(context_block, str) or not context_block.strip():
            return None

        text_prompt = content_of(message).strip()
        if not text_prompt:
            return None
        return _inject_context(text_prompt, context_block)

    @hookimpl
    async def save_state(
        self,
        session_id: str,
        state: State,
        message: Envelope,
        model_output: str,
    ) -> None:
        """Write model output into the contextseek evolution pipeline."""
        client = self._get_client()
        if client is None or not model_output:
            return

        scope = str(state.get("_contextseek_scope") or self._scope_from_message(message, session_id))
        try:
            await asyncio.to_thread(
                client.add,
                model_output,
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
    prompt: str,
    context_block: str,
) -> str:
    return f"{context_block}\n\n{prompt}"
