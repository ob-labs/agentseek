from __future__ import annotations

import sys
from typing import Literal

import logfire
import logfire.integrations.loguru as logfire_loguru
import typer

from agentseek.cli import apply_agentseek_cli_overrides
from agentseek.env import (
    agentseek_config_file,
    apply_agentseek_env_aliases,
    get_agentseek_settings,
)

apply_agentseek_env_aliases()
apply_agentseek_cli_overrides()


def _logfire_console_config(enabled: bool) -> logfire.ConsoleOptions | Literal[False]:
    if not enabled:
        return False

    return logfire.ConsoleOptions()


def _instrument_agentseek() -> None:
    from loguru import logger

    logger.remove()
    logger.add(sys.stderr, colorize=True)

    settings = get_agentseek_settings()
    logfire.configure(send_to_logfire=False, console=_logfire_console_config(settings.console))
    logger.add(logfire_loguru.LogfireHandler(), format="{message}")


def create_cli_app() -> typer.Typer:
    from bub.framework import BubFramework

    _instrument_agentseek()
    framework = BubFramework(config_file=agentseek_config_file())
    framework.load_hooks()
    app = framework.create_cli_app()

    if not app.registered_commands:

        @app.command("help")
        def _help() -> None:
            typer.echo("No CLI command loaded.")

    _register_version_command(app)
    return app


def _register_version_command(app: typer.Typer) -> None:
    """Register ``version`` if not already provided by agentseek-cli plugin."""
    existing = {getattr(c, "name", None) for c in app.registered_commands}
    if "version" in existing:
        return

    from agentseek.cli import agentseek_version

    @app.command("version")
    def version_cmd() -> None:
        """Show version information."""
        typer.echo(f"agentseek {agentseek_version()}")


app = create_cli_app()

__all__ = ["app", "create_cli_app"]


if __name__ == "__main__":
    app()
