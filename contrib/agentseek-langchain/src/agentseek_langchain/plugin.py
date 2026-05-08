from __future__ import annotations

from collections.abc import AsyncIterable, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import replace
from typing import Any, cast
from uuid import uuid4

from bub.hookspecs import hookimpl
from bub.types import State
from bub.utils import workspace_from_state
from loguru import logger
from republic import AsyncStreamEvents, StreamEvent, StreamState, TapeEntry, ToolContext

from .bridge import (
    LangchainFactoryRequest,
    LangchainRunContext,
    RunnableBinding,
    build_runnable_config,
)
from .config import LangchainPluginSettings, load_settings
from .loader import resolve_runnable_binding
from .tape_recorder import LangchainTapeCallbackHandler
from .tools import bub_registry_to_langchain_tools


class LangchainPlugin:
    """Route Bub ``run_model`` through a LangChain Runnable."""

    def __init__(self, framework: Any) -> None:
        self.framework = framework

    def _load_settings(self, prompt: str | list[dict[str, Any]]) -> LangchainPluginSettings | None:
        settings = load_settings()
        factory = (settings.factory or "").strip()
        if not factory:
            return None
        settings.factory = factory
        if isinstance(prompt, str) and prompt.strip().startswith(","):
            return None
        return settings

    def _build_langchain_tools(
        self,
        *,
        settings: LangchainPluginSettings,
        state: State,
        session_id: str,
        tape_name: str | None,
    ) -> tuple[list[Any], LangchainRunContext]:
        run_context = LangchainRunContext(
            session_id=session_id,
            tape_name=tape_name,
            run_id=f"langchain-{uuid4().hex}",
        )
        if not settings.include_bub_tools:
            return [], run_context
        tool_context = ToolContext(
            tape=tape_name,
            run_id=run_context.run_id,
            state=state,
        )
        return bub_registry_to_langchain_tools(tool_context=tool_context), run_context

    def _bind_logger(self, run_context: LangchainRunContext):
        return logger.bind(**run_context.as_logger_extra())

    @asynccontextmanager
    async def _forked_session_tape(
        self,
        *,
        runtime_agent: Any,
        session_id: str,
        state: State,
    ) -> AsyncIterator[tuple[str, Any]]:
        session_tape = runtime_agent.tapes.session_tape(session_id, workspace_from_state(state))
        session_tape.context = replace(session_tape.context, state=state)
        merge_back = not session_id.startswith("temp/")
        async with runtime_agent.tapes.fork_tape(session_tape.name, merge_back=merge_back):
            await runtime_agent.tapes.ensure_bootstrap_anchor(session_tape.name)
            yield session_tape.name, session_tape

    @asynccontextmanager
    async def _session_tape_scope(
        self,
        *,
        settings: LangchainPluginSettings,
        runtime_agent: Any,
        session_id: str,
        state: State,
    ) -> AsyncIterator[tuple[str | None, Any | None]]:
        if runtime_agent is None or not settings.tape:
            yield None, None
            return

        async with self._forked_session_tape(
            runtime_agent=runtime_agent,
            session_id=session_id,
            state=state,
        ) as (tape_name, session_tape):
            yield tape_name, session_tape

    def _build_callbacks(
        self,
        *,
        settings: LangchainPluginSettings,
        session_tape: Any | None,
        run_context: LangchainRunContext,
    ) -> list[Any]:
        if not settings.tape or session_tape is None:
            return []
        return [
            LangchainTapeCallbackHandler(
                session_tape,
                session_id=run_context.session_id,
                tape_name=run_context.tape_name,
                root_run_id=run_context.run_id,
            )
        ]

    def _prepare_invocation(
        self,
        *,
        settings: LangchainPluginSettings,
        prompt: str | list[dict[str, Any]],
        session_id: str,
        state: State,
        tape_name: str | None,
        session_tape: Any | None,
    ) -> tuple[LangchainFactoryRequest, RunnableBinding, dict[str, Any]]:
        langchain_tools, run_context = self._build_langchain_tools(
            settings=settings,
            state=state,
            session_id=session_id,
            tape_name=tape_name,
        )
        request = LangchainFactoryRequest(
            state=state,
            session_id=session_id,
            workspace=workspace_from_state(state),
            tools=langchain_tools,
            system_prompt=self.framework.get_system_prompt(prompt, state),
            prompt=prompt,
            langchain_context=run_context,
        )
        bound_logger = self._bind_logger(run_context)
        bound_logger.debug("Resolving LangChain runnable factory={}", settings.factory)
        binding = resolve_runnable_binding(
            cast(str, settings.factory),
            request,
        )
        bound_logger.debug("Resolved LangChain runnable")
        callbacks = self._build_callbacks(
            settings=settings,
            session_tape=session_tape,
            run_context=request.langchain_context,
        )
        config = build_runnable_config(
            langchain_context=request.langchain_context,
            callbacks=callbacks,
        )
        return request, binding, config

    async def _invoke_binding(
        self,
        binding: RunnableBinding,
        *,
        config: dict[str, Any],
    ) -> str:
        output = await binding.runnable.ainvoke(
            binding.invoke_input,
            config=config,
        )
        parser = binding.output_parser
        if parser is None:
            raise RuntimeError("RunnableBinding.output_parser must be resolved before execution")
        return parser(output)

    async def _stream_binding(
        self,
        binding: RunnableBinding,
        *,
        config: dict[str, Any],
    ) -> AsyncIterable[str]:
        astream = getattr(binding.runnable, "astream", None)
        if not callable(astream) or binding.stream_parser is None:
            yield await self._invoke_binding(binding, config=config)
            return

        async for chunk in astream(binding.invoke_input, config=config):
            text = binding.stream_parser(chunk)
            if text:
                yield text

    async def _append_tape_message(
        self,
        session_tape: Any | None,
        *,
        role: str,
        content: str,
    ) -> None:
        if session_tape is None:
            return
        await session_tape.append_async(TapeEntry.message({"role": role, "content": content}))

    async def _invoke_runnable(
        self,
        *,
        settings: LangchainPluginSettings,
        prompt: str | list[dict[str, Any]],
        session_id: str,
        state: State,
        tape_name: str | None,
        session_tape: Any | None,
    ) -> str:
        request, binding, config = self._prepare_invocation(
            settings=settings,
            prompt=prompt,
            session_id=session_id,
            state=state,
            tape_name=tape_name,
            session_tape=session_tape,
        )
        bound_logger = self._bind_logger(request.langchain_context)
        await self._append_tape_message(
            session_tape,
            role="user",
            content=request.prompt_text,
        )

        bound_logger.debug("Invoking LangChain runnable")
        normalized = await self._invoke_binding(binding, config=config)
        bound_logger.debug("LangChain runnable completed")

        await self._append_tape_message(
            session_tape,
            role="assistant",
            content=normalized,
        )
        return normalized

    async def _stream_runnable(
        self,
        *,
        settings: LangchainPluginSettings,
        prompt: str | list[dict[str, Any]],
        session_id: str,
        state: State,
        tape_name: str | None,
        session_tape: Any | None,
    ) -> AsyncStreamEvents:
        request, binding, config = self._prepare_invocation(
            settings=settings,
            prompt=prompt,
            session_id=session_id,
            state=state,
            tape_name=tape_name,
            session_tape=session_tape,
        )
        bound_logger = self._bind_logger(request.langchain_context)

        async def iterator():
            assistant_parts: list[str] = []
            await self._append_tape_message(
                session_tape,
                role="user",
                content=request.prompt_text,
            )
            astream = getattr(binding.runnable, "astream", None)
            if callable(astream) and binding.stream_parser is not None:
                bound_logger.debug("Streaming LangChain runnable")
            elif callable(astream):
                bound_logger.debug("Runnable has no stream parser; falling back to ainvoke for stable final output")
            else:
                bound_logger.debug("LangChain runnable has no astream; falling back to ainvoke")

            async for text in self._stream_binding(binding, config=config):
                assistant_parts.append(text)
                yield StreamEvent("text", {"delta": text})

            final_text = "".join(assistant_parts)
            bound_logger.debug("LangChain stream completed")
            await self._append_tape_message(
                session_tape,
                role="assistant",
                content=final_text,
            )
            yield StreamEvent("final", {"text": final_text, "ok": True})

        return AsyncStreamEvents(iterator(), state=StreamState())

    @hookimpl(tryfirst=True)
    async def run_model(self, prompt: str | list[dict[str, Any]], session_id: str, state: State) -> str | None:
        settings = self._load_settings(prompt)
        if settings is None:
            return None

        async with self._session_tape_scope(
            settings=settings,
            runtime_agent=state.get("_runtime_agent"),
            session_id=session_id,
            state=state,
        ) as (tape_name, session_tape):
            return await self._invoke_runnable(
                settings=settings,
                prompt=prompt,
                session_id=session_id,
                state=state,
                tape_name=tape_name,
                session_tape=session_tape,
            )

    @hookimpl(tryfirst=True)
    async def run_model_stream(
        self,
        prompt: str | list[dict[str, Any]],
        session_id: str,
        state: State,
    ) -> AsyncStreamEvents | None:
        settings = self._load_settings(prompt)
        if settings is None:
            return None

        async def iterator():
            async with self._session_tape_scope(
                settings=settings,
                runtime_agent=state.get("_runtime_agent"),
                session_id=session_id,
                state=state,
            ) as (tape_name, session_tape):
                stream = await self._stream_runnable(
                    settings=settings,
                    prompt=prompt,
                    session_id=session_id,
                    state=state,
                    tape_name=tape_name,
                    session_tape=session_tape,
                )
                async for event in stream:
                    yield event

        return AsyncStreamEvents(iterator(), state=StreamState())


main = LangchainPlugin
