from __future__ import annotations

import asyncio
import importlib.util

import pytest
from agentseek_langchain.plugin import LangchainPlugin

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("langchain_core") is None,
    reason="langchain_core is not installed in the root test environment",
)


class _Framework:
    def get_system_prompt(self, prompt: str | list[dict[str, str]], state: dict[str, str]) -> str:
        return "You are a helpful assistant"


def test_minimal_runnable_factory_works_through_plugin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BUB_LANGCHAIN_MODE", "runnable")
    monkeypatch.setenv("BUB_LANGCHAIN_FACTORY", "agentseek_langchain_examples.minimal_runnable:minimal_lc_agent")
    monkeypatch.setenv("BUB_LANGCHAIN_INCLUDE_BUB_TOOLS", "false")
    monkeypatch.setenv("BUB_LANGCHAIN_TAPE", "false")

    plugin = LangchainPlugin(_Framework())
    result = asyncio.run(plugin.run_model("hello from minimal", session_id="session-minimal", state={}))

    assert result == "[minimal_lc_agent] hello from minimal\nSystem: You are a helpful assistant"
