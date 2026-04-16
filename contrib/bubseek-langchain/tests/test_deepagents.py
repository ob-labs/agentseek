from __future__ import annotations

import asyncio
import importlib
import sys
import textwrap
from pathlib import Path
from typing import Any

import pytest
from bubseek_langchain.plugin import LangchainPlugin

pytest.importorskip("deepagents")


class _Framework:
    def get_system_prompt(self, prompt: str | list[dict[str, Any]], state: dict[str, Any]) -> str:
        return "system prompt"


def _write_module(tmp_path: Path, module_name: str, source: str) -> None:
    (tmp_path / f"{module_name}.py").write_text(textwrap.dedent(source), encoding="utf-8")
    sys.modules.pop(module_name, None)
    importlib.invalidate_caches()


def test_run_model_with_deepagents_factory(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.setenv("BUB_LANGCHAIN_MODE", "runnable")
    monkeypatch.setenv("BUB_LANGCHAIN_FACTORY", "lc_deepagents_factory:factory")
    monkeypatch.setenv("BUB_LANGCHAIN_INCLUDE_BUB_TOOLS", "false")
    monkeypatch.setenv("BUB_LANGCHAIN_TAPE", "false")

    _write_module(
        tmp_path,
        "lc_deepagents_factory",
        """
        from typing import Any, Sequence

        from deepagents import create_deep_agent
        from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
        from langchain_core.messages import AIMessage
        from langchain_core.runnables import RunnableLambda

        from bubseek_langchain.bridge import extract_prompt_text


        class ToolReadyFakeChatModel(FakeMessagesListChatModel):
            def bind_tools(
                self,
                tools: Sequence[dict[str, Any] | type | Any],
                *,
                tool_choice: str | None = None,
                **kwargs: Any,
            ):
                return self


        def factory(*, prompt, tools, system_prompt, **kwargs):
            agent = create_deep_agent(
                model=ToolReadyFakeChatModel(responses=[AIMessage(content="deep ok")]),
                tools=tools or [],
                system_prompt=system_prompt,
                subagents=[],
                memory=None,
            )
            runnable = agent | RunnableLambda(lambda state: state["messages"][-1].content)
            return runnable, {"messages": [{"role": "user", "content": extract_prompt_text(prompt)}]}
        """,
    )

    plugin = LangchainPlugin(_Framework())
    result = asyncio.run(plugin.run_model("hello deepagents", session_id="session-deepagents", state={}))

    assert result == "deep ok"
