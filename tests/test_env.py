from __future__ import annotations

import os

from agentseek.env import (
    DEFAULT_AGENTSEEK_CONFIG,
    DEFAULT_AGENTSEEK_HOME,
    DEFAULT_PLUGIN_SANDBOX,
    agentseek_config_file,
    apply_agentseek_env_aliases,
)


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


def test_agentseek_defaults_bub_home_to_agentseek_home(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUB_HOME", raising=False)
    monkeypatch.delenv("AGENTSEEK_HOME", raising=False)

    apply_agentseek_env_aliases()

    assert os.environ["BUB_HOME"] == str(tmp_path / DEFAULT_AGENTSEEK_HOME)
    assert agentseek_config_file() == (tmp_path / DEFAULT_AGENTSEEK_HOME / DEFAULT_AGENTSEEK_CONFIG).resolve()


def test_agentseek_home_alias_fills_missing_bub_home(monkeypatch, tmp_path) -> None:
    agentseek_home = tmp_path / "agentseek-home"
    monkeypatch.delenv("BUB_HOME", raising=False)
    monkeypatch.setenv("AGENTSEEK_HOME", str(agentseek_home))

    apply_agentseek_env_aliases()

    assert os.environ["BUB_HOME"] == str(agentseek_home)


def test_existing_bub_home_takes_precedence(monkeypatch, tmp_path) -> None:
    bub_home = tmp_path / "bub-home"
    agentseek_home = tmp_path / "agentseek-home"
    monkeypatch.setenv("BUB_HOME", str(bub_home))
    monkeypatch.setenv("AGENTSEEK_HOME", str(agentseek_home))

    apply_agentseek_env_aliases()

    assert os.environ["BUB_HOME"] == str(bub_home)


def test_agentseek_defaults_bub_project_under_home(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("BUB_PROJECT", raising=False)
    monkeypatch.delenv("AGENTSEEK_PROJECT", raising=False)
    monkeypatch.delenv("BUB_HOME", raising=False)

    apply_agentseek_env_aliases()

    assert os.environ["BUB_PROJECT"] == str(tmp_path / DEFAULT_AGENTSEEK_HOME / DEFAULT_PLUGIN_SANDBOX)


def test_existing_bub_project_takes_precedence(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BUB_PROJECT", str(tmp_path / "custom-project"))
    monkeypatch.delenv("AGENTSEEK_PROJECT", raising=False)
    monkeypatch.delenv("BUB_HOME", raising=False)

    apply_agentseek_env_aliases()

    assert os.environ["BUB_PROJECT"] == str(tmp_path / "custom-project")


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
