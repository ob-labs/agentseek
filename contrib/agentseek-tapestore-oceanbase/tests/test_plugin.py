from __future__ import annotations

from pathlib import Path

import agentseek_tapestore_oceanbase.plugin as plugin
from agentseek_tapestore_oceanbase.plugin import OceanBaseTapeStorePlugin, OceanBaseTapeStoreSettings
from agentseek_tapestore_oceanbase.store import OceanBaseTapeStore
from bub_tapestore_sqlalchemy.store import SQLAlchemyTapeStore


class _PluginManagerStub:
    def __init__(self) -> None:
        self.unregistered_names: list[str] = []
        self.registered_names: list[str] = []

    def unregister(self, *, name: str) -> None:
        self.unregistered_names.append(name)

    def register(self, plugin: object, *, name: str | None = None) -> object:
        del plugin
        if name is not None:
            self.registered_names.append(name)
        return object()


class _FrameworkStub:
    def __init__(self) -> None:
        self._plugin_manager = _PluginManagerStub()


def test_base_settings_default_to_bub_home(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BUB_HOME", str(tmp_path))
    monkeypatch.delenv("BUB_TAPESTORE_SQLALCHEMY_URL", raising=False)

    settings = plugin.SQLAlchemyTapeStoreSettings.from_env()

    assert settings.resolved_url.startswith("sqlite+pysqlite:///")
    assert settings.resolved_url.endswith("/tapes.db")
    assert str(tmp_path) in settings.resolved_url


def test_config_reads_oceanbase_vector_settings(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("BUB_HOME", str(tmp_path / "runtime-home"))
    monkeypatch.delenv("BUB_TAPESTORE_SQLALCHEMY_URL", raising=False)
    (tmp_path / ".env").write_text(
        "\n".join([
            "AGENTSEEK_TAPESTORE_OCEANBASE_EMBEDDING_MODEL=openai:text-embedding-3-small",
            "AGENTSEEK_TAPESTORE_OCEANBASE_VECTOR_METRIC=l2",
        ])
        + "\n",
        encoding="utf-8",
    )

    settings = OceanBaseTapeStoreSettings.from_env()

    assert settings.embedding_model == "openai:text-embedding-3-small"
    assert settings.vector_metric == "l2"


def test_plugin_provides_singleton_store(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(
        "BUB_TAPESTORE_SQLALCHEMY_URL",
        f"sqlite+pysqlite:///{tmp_path / 'custom.db'}",
    )
    plugin._store.cache_clear()

    store = plugin.provide_tape_store()

    assert isinstance(store, OceanBaseTapeStore)
    assert store is plugin.provide_tape_store()


def test_tape_store_from_env_returns_fresh_store(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(
        "BUB_TAPESTORE_SQLALCHEMY_URL",
        f"sqlite+pysqlite:///{tmp_path / 'fresh.db'}",
    )

    first = plugin.tape_store_from_env()
    second = plugin.tape_store_from_env()

    assert isinstance(first, OceanBaseTapeStore)
    assert isinstance(second, OceanBaseTapeStore)
    assert first is not second


def test_store_is_sqlalchemy_store_subclass() -> None:
    assert issubclass(OceanBaseTapeStore, SQLAlchemyTapeStore)


def test_plugin_unregisters_upstream_sqlalchemy_provider() -> None:
    framework = _FrameworkStub()

    OceanBaseTapeStorePlugin(framework)

    assert framework._plugin_manager.unregistered_names == ["tapestore-sqlalchemy"]


def test_plugin_blocks_future_upstream_sqlalchemy_registration() -> None:
    framework = _FrameworkStub()

    OceanBaseTapeStorePlugin(framework)
    framework._plugin_manager.register(object(), name="tapestore-sqlalchemy")
    framework._plugin_manager.register(object(), name="tapestore-oceanbase")

    assert framework._plugin_manager.registered_names == ["tapestore-oceanbase"]


def test_onboard_config_collects_oceanbase_vector_settings(monkeypatch) -> None:
    answers = iter([True, "openai:text-embedding-3-small", "l2"])
    monkeypatch.setattr(plugin.bub_inquirer, "ask_confirm", lambda *args, **kwargs: next(answers))
    monkeypatch.setattr(plugin.bub_inquirer, "ask_text", lambda *args, **kwargs: next(answers))

    assert plugin.onboard_config({}) == {
        "tapestore-oceanbase": {
            "embedding_model": "openai:text-embedding-3-small",
            "vector_metric": "l2",
        }
    }
