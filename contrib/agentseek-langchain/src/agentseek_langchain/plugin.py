from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from bub import hookimpl
from bub.types import State
from republic import AsyncStreamEvents, StreamEvent, StreamState

from agentseek_langchain.ag_ui import runtime_context_from_state
from agentseek_langchain.api_cli import register_api_commands
from agentseek_langchain.config import get_langchain_settings
from agentseek_langchain.loader import load_spec_from_path
from agentseek_langchain.spec import InvocationContext


class LangChainRunnablePlugin:
    def __init__(self) -> None:
        self._spec_cache = None

    def _get_spec(self):
        if self._spec_cache is None:
            settings = get_langchain_settings()
            self._spec_cache = load_spec_from_path(settings.SPEC)
        return self._spec_cache

    def _build_context(self, prompt: str | list[dict[str, Any]], session_id: str, state: State) -> InvocationContext:
        workspace_value = state.get("_runtime_workspace")
        workspace = Path(str(workspace_value)).resolve() if workspace_value else Path.cwd().resolve()
        return InvocationContext(
            prompt=prompt,
            session_id=session_id,
            state=state,
            workspace=workspace,
            agents_md=self._read_agents_md(workspace),
            runtime_context=runtime_context_from_state(state),
        )

    @staticmethod
    def _read_agents_md(workspace: Path) -> str | None:
        path = workspace / "AGENTS.md"
        if not path.is_file():
            return None
        try:
            content = path.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        return content or None

    @hookimpl(tryfirst=True)
    async def run_model(self, prompt: str | list[dict[str, Any]], session_id: str, state: State) -> str:
        return await self._get_spec().invoke(self._build_context(prompt, session_id, state))

    @hookimpl(tryfirst=True)
    async def run_model_stream(
        self,
        prompt: str | list[dict[str, Any]],
        session_id: str,
        state: State,
    ) -> AsyncStreamEvents:
        context = self._build_context(prompt, session_id, state)
        stream_state = StreamState()

        async def iterator():
            chunks: list[str] = []
            async for chunk in self._get_spec().stream(context):
                chunks.append(chunk)
                yield StreamEvent("text", {"delta": chunk})
            yield StreamEvent("final", {"text": "".join(chunks), "ok": True})

        return AsyncStreamEvents(iterator(), state=stream_state)

    @hookimpl
    def register_cli_commands(self, app: typer.Typer) -> None:
        register_api_commands(app)


main = LangChainRunnablePlugin()
