from __future__ import annotations

import asyncio
import sys
from collections.abc import Callable, Sequence
from types import ModuleType
from typing import Any

import pytest
from bubseek_langchain.plugin import LangchainPlugin

pytest.importorskip("deepagents")


class _Framework:
    def get_system_prompt(self, prompt: str | list[dict[str, Any]], state: dict[str, Any]) -> str:
        return "system prompt"


def test_build_chat_model_uses_bub_env(monkeypatch: pytest.MonkeyPatch) -> None:
    from examples.langchain import deepagents_dashscope

    captured: dict[str, Any] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    fake_module = ModuleType("langchain_openai")
    fake_module.__dict__["ChatOpenAI"] = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", fake_module)
    monkeypatch.setenv("BUB_MODEL", "glm-5.1")
    monkeypatch.setenv("BUB_API_KEY", "dashscope-key")
    monkeypatch.setenv("BUB_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    model = deepagents_dashscope._build_chat_model()

    assert isinstance(model, FakeChatOpenAI)
    assert captured == {
        "model": "glm-5.1",
        "api_key": "dashscope-key",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "temperature": 0,
    }


def test_run_model_with_deepagents_factory(monkeypatch: pytest.MonkeyPatch) -> None:
    from langchain_core.language_models.base import LanguageModelInput
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import Runnable
    from langchain_core.tools import BaseTool

    from examples.langchain import deepagents_dashscope

    class ToolReadyFakeChatModel(FakeMessagesListChatModel):
        def bind_tools(
            self,
            tools: Sequence[dict[str, Any] | type | Callable[..., Any] | BaseTool],
            *,
            tool_choice: str | None = None,
            **kwargs: Any,
        ) -> Runnable[LanguageModelInput, AIMessage]:
            return self

    monkeypatch.setenv("BUB_LANGCHAIN_MODE", "runnable")
    monkeypatch.setenv("BUB_LANGCHAIN_FACTORY", "examples.langchain.deepagents_dashscope:dashscope_deep_agent")
    monkeypatch.setenv("BUB_LANGCHAIN_INCLUDE_BUB_TOOLS", "false")
    monkeypatch.setenv("BUB_LANGCHAIN_TAPE", "false")
    monkeypatch.setattr(
        deepagents_dashscope,
        "_build_chat_model",
        lambda: ToolReadyFakeChatModel(responses=[AIMessage(content="deep ok")]),
    )

    plugin = LangchainPlugin(_Framework())
    result = asyncio.run(plugin.run_model("hello deepagents", session_id="session-deepagents", state={}))

    assert result == "deep ok"
