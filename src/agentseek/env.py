from __future__ import annotations

import os
from collections.abc import Mapping, MutableMapping
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import DotEnvSettingsSource, EnvSettingsSource, PydanticBaseSettingsSource

AGENTSEEK_ENV_PREFIX = "AGENTSEEK_"
BUB_ENV_PREFIX = "BUB_"

# Default layout when ``BUB_HOME`` / ``AGENTSEEK_HOME`` are unset: ``cwd / DEFAULT_AGENTSEEK_HOME``.
DEFAULT_AGENTSEEK_HOME = ".agentseek"

# Basename of Bub config under ``BUB_HOME``.
DEFAULT_AGENTSEEK_CONFIG = "config.yml"

# Under ``BUB_HOME`` for ``agentseek install`` when ``BUB_PROJECT`` / ``AGENTSEEK_PROJECT`` are unset.
# Must match ``uv init --name`` in ``apply_agentseek_install_project_defaults`` (cli.py).
DEFAULT_PLUGIN_SANDBOX = "agentseek-project"


class AgentseekAliasSource(PydanticBaseSettingsSource):
    """Build BUB_* aliases from AGENTSEEK_* settings sources."""

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        del field, field_name
        return None, "", False

    def __call__(self) -> dict[str, Any]:
        aliases: dict[str, str] = {}
        for env_vars in (
            DotEnvSettingsSource(self.settings_cls).env_vars,
            EnvSettingsSource(self.settings_cls).env_vars,
        ):
            aliases.update(_bub_aliases(env_vars))
        return {"aliases": aliases}


class AgentseekEnvironmentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    aliases: dict[str, str] = Field(default_factory=dict)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        del init_settings, env_settings, dotenv_settings, file_secret_settings
        return (AgentseekAliasSource(settings_cls),)


def apply_agentseek_env_aliases(environ: MutableMapping[str, str] | None = None) -> None:
    """Let AGENTSEEK_* variables act as fallbacks for BUB_* variables.

    Also applies agentseek defaults for ``BUB_HOME`` (see ``DEFAULT_AGENTSEEK_HOME``) and
    ``BUB_PROJECT`` (under that home, see ``DEFAULT_PLUGIN_SANDBOX``) when unset.
    """
    target_environ = os.environ if environ is None else environ
    for name, value in AgentseekEnvironmentSettings().aliases.items():
        target_environ.setdefault(name, value)
    _apply_agentseek_bub_location_defaults(target_environ)


def _apply_agentseek_bub_location_defaults(target_environ: MutableMapping[str, str]) -> None:
    """Set ``BUB_HOME`` then ``BUB_PROJECT`` only when missing (``setdefault``)."""
    target_environ.setdefault("BUB_HOME", _default_bub_home_for_agentseek())
    bub_home = Path(target_environ["BUB_HOME"]).expanduser()
    plugin_root = bub_home / DEFAULT_PLUGIN_SANDBOX
    target_environ.setdefault("BUB_PROJECT", str(plugin_root))


def _default_bub_home_for_agentseek() -> str:
    """String path Bub uses as ``BUB_HOME`` when the user has not set ``BUB_HOME`` / ``AGENTSEEK_HOME``."""
    return str(default_agentseek_home())


def agentseek_config_file() -> Path:
    bub_home = Path(os.environ["BUB_HOME"]).expanduser()
    return (bub_home / DEFAULT_AGENTSEEK_CONFIG).resolve()


def default_agentseek_home() -> Path:
    """Resolved directory for Bub runtime home when ``BUB_HOME`` is unset."""
    return Path.cwd() / DEFAULT_AGENTSEEK_HOME


def _bub_aliases(env_vars: Mapping[str, str | None]) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for name, value in env_vars.items():
        if not name.startswith(AGENTSEEK_ENV_PREFIX) or value is None:
            continue

        suffix = name.removeprefix(AGENTSEEK_ENV_PREFIX)
        if suffix:
            aliases[f"{BUB_ENV_PREFIX}{suffix}"] = value
    return aliases
