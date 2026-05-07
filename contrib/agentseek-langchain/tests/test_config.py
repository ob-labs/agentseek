from __future__ import annotations

import pytest
from agentseek_langchain.config import (
    LangchainPluginSettings,
    load_agent_protocol_settings,
    validate_config,
)
from agentseek_langchain.errors import LangchainConfigError


def test_validate_runnable_requires_factory() -> None:
    settings = LangchainPluginSettings(mode="runnable", factory=None)
    with pytest.raises(LangchainConfigError, match="BUB_LANGCHAIN_FACTORY"):
        validate_config(settings)


def test_validate_runnable_ok_with_factory() -> None:
    settings = LangchainPluginSettings(mode="runnable", factory="builtins:str")
    validate_config(settings)


def test_agentseek_aliases_work(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTSEEK_LANGCHAIN_MODE", "runnable")
    monkeypatch.setenv("AGENTSEEK_LANGCHAIN_FACTORY", "builtins:str")
    monkeypatch.setenv("AGENTSEEK_AGENT_PROTOCOL_URL", "http://remote")
    monkeypatch.setenv("AGENTSEEK_AGENT_PROTOCOL_AGENT_ID", "agent")

    settings = LangchainPluginSettings()
    protocol_settings = load_agent_protocol_settings()

    assert settings.mode == "runnable"
    assert settings.factory == "builtins:str"
    assert protocol_settings.url == "http://remote"
    assert protocol_settings.agent_id == "agent"


def test_bub_alias_wins_over_agentseek(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTSEEK_LANGCHAIN_FACTORY", "ignored:factory")
    monkeypatch.setenv("BUB_LANGCHAIN_FACTORY", "builtins:str")

    settings = LangchainPluginSettings()

    assert settings.factory == "builtins:str"
