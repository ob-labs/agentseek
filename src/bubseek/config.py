"""Configuration via pydantic-settings."""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_SETTINGS_CONFIG = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
)


class DatabaseSettings(BaseSettings):
    """Database connection settings for tape store (OceanBase/SeekDB or SQLite)."""

    model_config = _SETTINGS_CONFIG

    tapestore_sqlalchemy_url: str = Field(default="", validation_alias="BUB_TAPESTORE_SQLALCHEMY_URL")
    oceanbase_host: str = Field(default="127.0.0.1", validation_alias="OCEANBASE_HOST")
    oceanbase_port: int = Field(default=2881, validation_alias="OCEANBASE_PORT")
    oceanbase_user: str = Field(default="root", validation_alias="OCEANBASE_USER")
    oceanbase_password: str = Field(default="", validation_alias="OCEANBASE_PASSWORD")
    oceanbase_database: str = Field(default="bub", validation_alias="OCEANBASE_DATABASE")

    def mysql_connection_params(self) -> tuple[str, int, str, str, str] | None:
        """Return (host, port, user, password, database) when using MySQL, else None."""
        url = self.tapestore_sqlalchemy_url or ""
        if not url or "mysql" not in url.lower():
            return None
        host = self.oceanbase_host
        port = self.oceanbase_port
        user = self.oceanbase_user
        password = self.oceanbase_password
        database = self.oceanbase_database
        try:
            parsed = urlparse(url)
            if parsed.hostname:
                host = parsed.hostname
            if parsed.port:
                port = parsed.port
            if parsed.username:
                user = parsed.username
            if parsed.password is not None:
                password = parsed.password
            if parsed.path and parsed.path.strip("/"):
                database = parsed.path.strip("/")
        except Exception:  # noqa: S110
            pass
        return host, port, user, password, database


class BubSeekSettings(BaseSettings):
    """Main bubseek configuration."""

    model_config = _SETTINGS_CONFIG

    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
