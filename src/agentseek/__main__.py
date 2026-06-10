from __future__ import annotations

import sys
from typing import Literal

import logfire
import logfire.integrations.loguru as logfire_loguru
import typer

from agentseek.cli import (
    AGENTSEEK_CLI_HELP,
    apply_agentseek_runtime_command_layout,
)
from agentseek.env import (
    agentseek_config_file,
    apply_agentseek_env_aliases,
    get_agentseek_settings,
)

apply_agentseek_env_aliases()


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
    apply_agentseek_runtime_command_layout(app)
    app.info.help = AGENTSEEK_CLI_HELP

    if not app.registered_commands:

        @app.command("help")
        def _help() -> None:
            typer.echo("No CLI command loaded.")

    _register_version_command(app)
    return app


def _register_version_command(app: typer.Typer) -> None:
    """Register ``version`` if it is not already present."""
    command_name = "version"
    if any(getattr(command, "name", None) == command_name for command in app.registered_commands):
        return

    from agentseek.cli import agentseek_version

    @app.command(command_name)
    def version_cmd() -> None:
        """Show version information."""
        typer.echo(f"agentseek {agentseek_version()}")


app = create_cli_app()

__all__ = ["app", "create_cli_app"]


if __name__ == "__main__":
    app()
