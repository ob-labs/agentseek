from __future__ import annotations

from typing import Any

import bub
from bub import inquirer as bub_inquirer
from pydantic import AliasChoices, Field
from pydantic_settings import SettingsConfigDict

CONFIG_NAME = "schedule"
DEFAULT_SCHEDULE_TABLENAME = "apscheduler_jobs"


@bub.config(name=CONFIG_NAME)
class ScheduleSQLAlchemySettings(bub.Settings):
    """Configuration for the APScheduler SQLAlchemy job store."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "BUB_SCHEDULE_SQLALCHEMY_URL",
            "AGENTSEEK_SCHEDULE_SQLALCHEMY_URL",
            "BUB_TAPESTORE_SQLALCHEMY_URL",
            "AGENTSEEK_TAPESTORE_SQLALCHEMY_URL",
        ),
    )
    tablename: str = Field(
        default=DEFAULT_SCHEDULE_TABLENAME,
        validation_alias=AliasChoices(
            "BUB_SCHEDULE_SQLALCHEMY_TABLENAME",
            "AGENTSEEK_SCHEDULE_SQLALCHEMY_TABLENAME",
        ),
    )


def get_schedule_settings() -> ScheduleSQLAlchemySettings:
    """Resolve schedule settings through Bub's registered config pipeline."""
    return bub.ensure_config(ScheduleSQLAlchemySettings)


def onboard_config(current_config: dict[str, Any]) -> dict[str, Any] | None:
    existing = current_config.get(CONFIG_NAME)
    configure = bub_inquirer.ask_confirm(
        "Configure schedule plugin",
        default=isinstance(existing, dict),
    )
    if not configure:
        return None

    current = existing if isinstance(existing, dict) else {}
    url = bub_inquirer.ask_text(
        "Schedule SQLAlchemy URL (optional)",
        default=str(current.get("url") or ""),
    )
    tablename = bub_inquirer.ask_text(
        "Schedule table name",
        default=str(current.get("tablename") or DEFAULT_SCHEDULE_TABLENAME),
    )

    config: dict[str, Any] = {"tablename": tablename}
    if url:
        config["url"] = url
    return {CONFIG_NAME: config}
