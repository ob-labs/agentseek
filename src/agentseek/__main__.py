from __future__ import annotations

import sys
from typing import Literal

import logfire
import logfire.integrations.loguru as logfire_loguru
import typer

from agentseek.cli import (
    AGENTSEEK_AGENT_MODE_HELP,
    AGENTSEEK_CLI_HELP,
    CliMode,
    agentseek_version,
    apply_agentseek_agent_command_layout,
    apply_agentseek_runtime_command_layout,
    register_app_profile_options,
    resolve_cli_mode,
)
from agentseek.cli.banner import format_agentseek_banner
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


def create_cli_app(argv: list[str] | None = None) -> typer.Typer:
    _instrument_agentseek()
    mode = resolve_cli_mode(sys.argv if argv is None else argv)
    if mode is CliMode.AGENT:
        return _create_agent_cli_app()
    return _create_app_cli_app()


def _create_app_cli_app() -> typer.Typer:
    app = typer.Typer(
        name="agentseek",
        help=_format_cli_help(AGENTSEEK_CLI_HELP),
        add_completion=False,
        no_args_is_help=True,
    )
    register_app_profile_options(app)
    apply_agentseek_runtime_command_layout(app)
    _register_version_command(app)
    return app


def _create_agent_cli_app() -> typer.Typer:
    from bub.framework import BubFramework

    framework = BubFramework(config_file=agentseek_config_file())
    framework.load_hooks()
    app = typer.Typer(
        name="agentseek",
        help=_format_cli_help(AGENTSEEK_AGENT_MODE_HELP),
        add_completion=False,
        no_args_is_help=False,
    )
    apply_agentseek_agent_command_layout(app, framework)
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
        typer.echo(format_agentseek_banner(agentseek_version()))


def _format_cli_help(summary: str) -> str:
    return f"\b\n{format_agentseek_banner(agentseek_version())}\n\n{summary}"


app = create_cli_app()

__all__ = ["app", "create_cli_app"]


if __name__ == "__main__":
    app()
