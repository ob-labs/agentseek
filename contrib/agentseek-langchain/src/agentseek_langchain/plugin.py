from __future__ import annotations

from functools import cached_property
from pathlib import Path
from typing import Any

from bub import hookimpl
from bub.types import State
from republic import AsyncStreamEvents, StreamEvent, StreamState

from agentseek_langchain.config import get_langchain_settings
from agentseek_langchain.loader import load_spec_from_path
from agentseek_langchain.spec import InvocationContext


class LangChainRunnablePlugin:
    @cached_property
    def _spec(self):
        settings = get_langchain_settings()
        return load_spec_from_path(settings.spec)

    def _build_context(self, prompt: str | list[dict[str, Any]], session_id: str, state: State) -> InvocationContext:
        workspace_value = state.get("_runtime_workspace")
        workspace = Path(str(workspace_value)).resolve() if workspace_value else Path.cwd().resolve()
        return InvocationContext(
            prompt=prompt,
            session_id=session_id,
            state=state,
            workspace=workspace,
            agents_md=self._read_agents_md(workspace),
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

    @hookimpl
    async def run_model(self, prompt: str | list[dict[str, Any]], session_id: str, state: State) -> str:
        return await self._spec.invoke(self._build_context(prompt, session_id, state))

    @hookimpl
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
            async for chunk in self._spec.stream(context):
                chunks.append(chunk)
                yield StreamEvent("text", {"delta": chunk})
            yield StreamEvent("final", {"text": "".join(chunks), "ok": True})

        return AsyncStreamEvents(iterator(), state=stream_state)


main = LangChainRunnablePlugin()
