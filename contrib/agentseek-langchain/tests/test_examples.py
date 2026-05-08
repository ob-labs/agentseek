from __future__ import annotations

import asyncio
import importlib
import importlib.util
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from agentseek_langchain.bridge import LangchainFactoryRequest, LangchainRunContext
from agentseek_langchain.plugin import LangchainPlugin

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("langchain_core") is None,
    reason="langchain_core is not installed in the root test environment",
)


class _Framework:
    def get_system_prompt(self, prompt: str | list[dict[str, Any]], state: dict[str, Any]) -> str:
        return "You are a helpful assistant"


def _deepagents_dashscope_example():
    pytest.importorskip("deepagents")
    return importlib.import_module("deepagents_dashscope")


def test_minimal_runnable_example_works_through_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUB_LANGCHAIN_FACTORY", "minimal_runnable:minimal_lc_agent")
    monkeypatch.setenv("BUB_LANGCHAIN_INCLUDE_BUB_TOOLS", "false")
    monkeypatch.setenv("BUB_LANGCHAIN_TAPE", "false")

    plugin = LangchainPlugin(_Framework())
    result = asyncio.run(plugin.run_model("hello from minimal", session_id="session-minimal", state={}))

    assert result == "[minimal_lc_agent] hello from minimal\nSystem: You are a helpful assistant"


def test_deepagents_example_builds_chat_model_from_bub_env(monkeypatch: pytest.MonkeyPatch) -> None:
    deepagents_dashscope = _deepagents_dashscope_example()

    captured: dict[str, Any] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    fake_module = ModuleType("langchain_openai")
    fake_module.__dict__["ChatOpenAI"] = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", fake_module)
    monkeypatch.setenv("BUB_MODEL", "openai:glm-5.1")
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


def test_deepagents_example_prefers_specific_env(monkeypatch: pytest.MonkeyPatch) -> None:
    deepagents_dashscope = _deepagents_dashscope_example()

    captured: dict[str, Any] = {}

    class FakeChatOpenAI:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    fake_module = ModuleType("langchain_openai")
    fake_module.__dict__["ChatOpenAI"] = FakeChatOpenAI
    monkeypatch.setitem(sys.modules, "langchain_openai", fake_module)
    monkeypatch.setenv("BUB_MODEL", "openai:gpt-4o")
    monkeypatch.setenv("BUB_API_KEY", "global-key")
    monkeypatch.setenv("BUB_API_BASE", "https://api.openai.com/v1")
    monkeypatch.setenv("BUB_DEEPAGENTS_MODEL", "glm-5.1")
    monkeypatch.setenv("BUB_DEEPAGENTS_API_KEY", "dashscope-key")
    monkeypatch.setenv("BUB_DEEPAGENTS_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    model = deepagents_dashscope._build_chat_model()

    assert isinstance(model, FakeChatOpenAI)
    assert captured == {
        "model": "glm-5.1",
        "api_key": "dashscope-key",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "temperature": 0,
    }


def test_deepagents_example_factory_works_through_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    from langchain_core.language_models.base import LanguageModelInput
    from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
    from langchain_core.messages import AIMessage
    from langchain_core.runnables import Runnable
    from langchain_core.tools import BaseTool

    deepagents_dashscope = _deepagents_dashscope_example()

    class ToolReadyFakeChatModel(FakeMessagesListChatModel):
        def bind_tools(
            self,
            tools: Sequence[dict[str, Any] | type | Callable[..., Any] | BaseTool],
            *,
            tool_choice: str | None = None,
            **kwargs: Any,
        ) -> Runnable[LanguageModelInput, AIMessage]:
            return self

    monkeypatch.setenv("BUB_LANGCHAIN_FACTORY", "deepagents_dashscope:dashscope_deep_agent")
    monkeypatch.setenv("BUB_LANGCHAIN_INCLUDE_BUB_TOOLS", "false")
    monkeypatch.setenv("BUB_LANGCHAIN_TAPE", "false")
    monkeypatch.setattr(
        deepagents_dashscope,
        "_build_chat_model",
        lambda _logger=None: ToolReadyFakeChatModel(responses=[AIMessage(content="deep ok")]),
    )

    plugin = LangchainPlugin(_Framework())
    result = asyncio.run(plugin.run_model("hello deepagents", session_id="session-deepagents", state={}))

    assert result == "deep ok"


def test_deepagents_example_binds_logger_context(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    from langchain_core.messages import AIMessage
    from langchain_core.runnables import RunnableLambda

    deepagents_dashscope = _deepagents_dashscope_example()

    captured: dict[str, Any] = {}

    class FakeBoundLogger:
        def info(self, message: str, *args: Any) -> None:
            captured.setdefault("info", []).append((message, args))

        def debug(self, message: str, *args: Any) -> None:
            captured.setdefault("debug", []).append((message, args))

    class FakeLogger:
        def bind(self, **kwargs: Any) -> FakeBoundLogger:
            captured["bind"] = kwargs
            return FakeBoundLogger()

    def fake_create_deep_agent(*, model: Any, tools: list[Any], system_prompt: str) -> RunnableLambda:
        captured["model"] = model
        captured["tools"] = tools
        captured["system_prompt"] = system_prompt
        return RunnableLambda(lambda state: {"messages": [SimpleNamespace(content=state["messages"][-1]["content"])]})

    fake_module = ModuleType("deepagents")
    fake_module.__dict__["create_deep_agent"] = fake_create_deep_agent

    monkeypatch.setitem(sys.modules, "deepagents", fake_module)
    monkeypatch.setattr(deepagents_dashscope, "logger", FakeLogger())
    monkeypatch.setattr(deepagents_dashscope, "_build_chat_model", lambda _logger: "fake-chat-model")

    context = LangchainRunContext(
        session_id="session-deepagents",
        tape_name="tape-deepagents",
        run_id="langchain-root",
    )
    request = LangchainFactoryRequest(
        state={},
        session_id="session-deepagents",
        workspace=Path("."),
        tools=[],
        system_prompt="system prompt",
        prompt="hello deepagents",
        langchain_context=context,
    )

    binding = deepagents_dashscope.dashscope_deep_agent(request=request)

    assert captured["bind"] == {
        "session_id": "session-deepagents",
        "tape_name": "tape-deepagents",
        "langchain_run_id": "langchain-root",
    }
    assert captured["model"] == "fake-chat-model"
    assert captured["system_prompt"] == "system prompt"
    assert binding.invoke_input == {"messages": [{"role": "user", "content": "hello deepagents"}]}
    assert binding.runnable.invoke(binding.invoke_input)["messages"][-1].content == "hello deepagents"
    assert binding.output_parser is not None
    assert binding.output_parser({"messages": [AIMessage(content="hello deepagents")]}) == "hello deepagents"
    assert captured["tools"][0]("Shanghai") == "It's always sunny in Shanghai!"
