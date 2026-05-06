from __future__ import annotations

import os

from agentseek.env import apply_agentseek_env_aliases


def test_agentseek_env_fills_missing_bub_env(monkeypatch) -> None:
    monkeypatch.delenv("BUB_MODEL", raising=False)
    monkeypatch.setenv("AGENTSEEK_MODEL", "openai:test-model")

    apply_agentseek_env_aliases()

    assert os.environ["BUB_MODEL"] == "openai:test-model"


def test_existing_bub_env_takes_precedence(monkeypatch) -> None:
    monkeypatch.setenv("BUB_API_KEY", "bub-key")
    monkeypatch.setenv("AGENTSEEK_API_KEY", "agentseek-key")

    apply_agentseek_env_aliases()

    assert os.environ["BUB_API_KEY"] == "bub-key"


def test_agentseek_dotenv_fills_missing_bub_env(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUB_TAPESTORE_SQLALCHEMY_URL", raising=False)
    monkeypatch.delenv("AGENTSEEK_TAPESTORE_SQLALCHEMY_URL", raising=False)
    (tmp_path / ".env").write_text(
        "AGENTSEEK_TAPESTORE_SQLALCHEMY_URL=sqlite+pysqlite:////tmp/agentseek.sqlite\n",
        encoding="utf-8",
    )

    apply_agentseek_env_aliases()

    assert os.environ["BUB_TAPESTORE_SQLALCHEMY_URL"] == "sqlite+pysqlite:////tmp/agentseek.sqlite"
