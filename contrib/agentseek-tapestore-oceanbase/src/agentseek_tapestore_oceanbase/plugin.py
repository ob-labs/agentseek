from __future__ import annotations

from contextlib import suppress
from functools import lru_cache
from typing import Any

import bub
from bub import hookimpl
from bub import inquirer as bub_inquirer
from bub_tapestore_sqlalchemy.plugin import SQLAlchemyTapeStoreSettings
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import SettingsConfigDict

from agentseek_tapestore_oceanbase.store import OceanBaseTapeStore
from agentseek_tapestore_oceanbase.vector_support import normalize_vector_metric

CONFIG_NAME = "tapestore-oceanbase"
UPSTREAM_TAPESTORE_PLUGIN_NAME = "tapestore-sqlalchemy"
REGISTER_GUARD_ATTR = "_agentseek_tapestore_oceanbase_register_guard"


@bub.config(name=CONFIG_NAME)
class OceanBaseTapeStoreSettings(bub.Settings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    embedding_model: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "BUB_TAPESTORE_OCEANBASE_EMBEDDING_MODEL",
            "AGENTSEEK_TAPESTORE_OCEANBASE_EMBEDDING_MODEL",
            "BUB_TAPESTORE_SQLALCHEMY_EMBEDDING_MODEL",
            "AGENTSEEK_TAPESTORE_SQLALCHEMY_EMBEDDING_MODEL",
        ),
    )
    vector_metric: str = Field(
        default="cosine",
        validation_alias=AliasChoices(
            "BUB_TAPESTORE_OCEANBASE_VECTOR_METRIC",
            "AGENTSEEK_TAPESTORE_OCEANBASE_VECTOR_METRIC",
            "BUB_TAPESTORE_SQLALCHEMY_VECTOR_METRIC",
            "AGENTSEEK_TAPESTORE_SQLALCHEMY_VECTOR_METRIC",
        ),
    )

    @classmethod
    def from_env(cls) -> OceanBaseTapeStoreSettings:
        return cls()

    @field_validator("embedding_model", mode="after")
    @classmethod
    def _normalize_embedding_model(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("vector_metric", mode="after")
    @classmethod
    def _normalize_vector_metric(cls, value: str) -> str:
        return normalize_vector_metric(value)


def build_store(
    base_settings: SQLAlchemyTapeStoreSettings | None = None,
    oceanbase_settings: OceanBaseTapeStoreSettings | None = None,
) -> OceanBaseTapeStore:
    resolved_base_settings = base_settings or bub.ensure_config(SQLAlchemyTapeStoreSettings)
    resolved_oceanbase_settings = oceanbase_settings or bub.ensure_config(OceanBaseTapeStoreSettings)
    return OceanBaseTapeStore(
        url=resolved_base_settings.resolved_url,
        echo=resolved_base_settings.echo,
        embedding_model=resolved_oceanbase_settings.embedding_model,
        vector_metric=resolved_oceanbase_settings.vector_metric,
    )


@lru_cache(maxsize=1)
def _store() -> OceanBaseTapeStore:
    return build_store()


def tape_store_from_env() -> OceanBaseTapeStore:
    return build_store(
        base_settings=SQLAlchemyTapeStoreSettings.from_env(),
        oceanbase_settings=OceanBaseTapeStoreSettings(),
    )


@hookimpl
def provide_tape_store() -> OceanBaseTapeStore:
    return _store()


@hookimpl
def onboard_config(current_config: dict[str, Any]) -> dict[str, Any] | None:
    existing = current_config.get(CONFIG_NAME)
    configure = bub_inquirer.ask_confirm(
        "Configure OceanBase vector enhancement",
        default=isinstance(existing, dict),
    )
    if not configure:
        return None

    current = existing if isinstance(existing, dict) else {}
    embedding_model = bub_inquirer.ask_text(
        "OceanBase embedding model (optional)",
        default=str(current.get("embedding_model") or ""),
    )
    vector_metric = bub_inquirer.ask_text(
        "OceanBase vector metric",
        default=str(current.get("vector_metric") or "cosine"),
    )

    config: dict[str, Any] = {
        "vector_metric": normalize_vector_metric(vector_metric),
    }
    if embedding_model:
        config["embedding_model"] = embedding_model
    return {CONFIG_NAME: config}


class OceanBaseTapeStorePlugin:
    def __init__(self, framework: object | None = None) -> None:
        self._prefer_oceanbase_provider(framework)

    @staticmethod
    def _prefer_oceanbase_provider(framework: object | None) -> None:
        if framework is None:
            return
        plugin_manager = getattr(framework, "_plugin_manager", None)
        if plugin_manager is None:
            return
        OceanBaseTapeStorePlugin._guard_upstream_registration(plugin_manager)
        with suppress(Exception):
            plugin_manager.unregister(name=UPSTREAM_TAPESTORE_PLUGIN_NAME)

    @staticmethod
    def _guard_upstream_registration(plugin_manager: Any) -> None:
        if getattr(plugin_manager, REGISTER_GUARD_ATTR, False):
            return
        original_register = getattr(plugin_manager, "register", None)
        if original_register is None:
            return

        def guarded_register(plugin: object, name: str | None = None):
            if name == UPSTREAM_TAPESTORE_PLUGIN_NAME:
                return plugin
            return original_register(plugin, name=name)

        plugin_manager.register = guarded_register
        setattr(plugin_manager, REGISTER_GUARD_ATTR, True)

    @hookimpl
    def provide_tape_store(self) -> OceanBaseTapeStore:
        return provide_tape_store()

    @hookimpl
    def onboard_config(self, current_config: dict[str, Any]) -> dict[str, Any] | None:
        return onboard_config(current_config)
