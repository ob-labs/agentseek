from __future__ import annotations

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AGUISettings(BaseSettings):
    """Runtime settings for the AG-UI gateway channel."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
    )

    host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("BUB_AG_UI_HOST", "AGENTSEEK_AG_UI_HOST"),
    )
    port: int = Field(
        default=8088,
        validation_alias=AliasChoices("BUB_AG_UI_PORT", "AGENTSEEK_AG_UI_PORT"),
    )
    path: str = Field(
        default="/agent",
        validation_alias=AliasChoices("BUB_AG_UI_PATH", "AGENTSEEK_AG_UI_PATH"),
    )
    health_path: str = Field(
        default="/agent/health",
        validation_alias=AliasChoices("BUB_AG_UI_HEALTH_PATH", "AGENTSEEK_AG_UI_HEALTH_PATH"),
    )


def load_settings() -> AGUISettings:
    return AGUISettings()
