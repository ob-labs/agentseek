from __future__ import annotations

import pytest
from agentseek_langchain.config import LangchainPluginSettings


def test_langchain_factory_agentseek_alias_works(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTSEEK_LANGCHAIN_FACTORY", "builtins:str")

    settings = LangchainPluginSettings()

    assert settings.factory == "builtins:str"


def test_bub_alias_wins_over_agentseek(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTSEEK_LANGCHAIN_FACTORY", "ignored:factory")
    monkeypatch.setenv("BUB_LANGCHAIN_FACTORY", "builtins:str")

    settings = LangchainPluginSettings()

    assert settings.factory == "builtins:str"
