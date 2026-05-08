from __future__ import annotations

import pytest
from agentseek_langchain.agent_protocol import load_agent_protocol_settings
from agentseek_langchain.config import LangchainPluginSettings


def test_agentseek_aliases_work(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTSEEK_LANGCHAIN_FACTORY", "builtins:str")
    monkeypatch.setenv("AGENTSEEK_AGENT_PROTOCOL_URL", "http://remote")
    monkeypatch.setenv("AGENTSEEK_AGENT_PROTOCOL_AGENT_ID", "agent")

    settings = LangchainPluginSettings()
    protocol_settings = load_agent_protocol_settings()

    assert settings.factory == "builtins:str"
    assert protocol_settings.url == "http://remote"
    assert protocol_settings.agent_id == "agent"


def test_bub_alias_wins_over_agentseek(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTSEEK_LANGCHAIN_FACTORY", "ignored:factory")
    monkeypatch.setenv("BUB_LANGCHAIN_FACTORY", "builtins:str")

    settings = LangchainPluginSettings()

    assert settings.factory == "builtins:str"
