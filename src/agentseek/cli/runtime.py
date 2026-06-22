"""AgentSeek CLI runtime profiles."""

from __future__ import annotations

from enum import StrEnum
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from typing import Annotated

import typer

from agentseek.cli.commands import chat, create, dev, doctor, info, task

AGENTSEEK_CLI_HELP = "AgentSeek is the Toolkit for App Development Lifecycle."
AGENTSEEK_AGENT_MODE_HELP = AGENTSEEK_CLI_HELP

PROJECT_COMMAND_PANEL = "Project"


class CliMode(StrEnum):
    CLI = "cli"
    AGENT = "agent"


def agentseek_version() -> str:
    try:
        return package_version("agentseek")
    except PackageNotFoundError:
        return "0.0.0"


def resolve_cli_mode(argv: list[str]) -> CliMode:
    """Resolve the requested root CLI profile from raw process arguments."""
    args = argv[1:]
    for index, arg in enumerate(args):
        if arg == "--mode" and index + 1 < len(args):
            return _parse_cli_mode(args[index + 1])
        if arg.startswith("--mode="):
            return _parse_cli_mode(arg.split("=", 1)[1])
    return CliMode.CLI


def _parse_cli_mode(value: str) -> CliMode:
    try:
        return CliMode(value.lower())
    except ValueError:
        typer.echo(f"Unsupported CLI mode: {value}. Expected one of: cli, agent.", err=True)
        raise typer.Exit(2) from None


def _clear_cli_surface(app: typer.Typer) -> None:
    app.registered_commands.clear()
    app.registered_groups.clear()


def apply_agentseek_runtime_command_layout(app: typer.Typer) -> None:
    """Mount the default app lifecycle command surface."""
    app.suggest_commands = False
    _clear_cli_surface(app)

    app.add_typer(create.app, name="create", rich_help_panel=PROJECT_COMMAND_PANEL)
    app.add_typer(dev.app, name="dev", rich_help_panel=PROJECT_COMMAND_PANEL)
    app.add_typer(info.app, name="info", rich_help_panel=PROJECT_COMMAND_PANEL)
    app.add_typer(doctor.app, name="doctor", rich_help_panel=PROJECT_COMMAND_PANEL)
    app.command(
        "task",
        rich_help_panel=PROJECT_COMMAND_PANEL,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True, "help_option_names": []},
        help="Run project duties through Duty's native parser.",
    )(task.task)


def register_app_profile_options(app: typer.Typer) -> None:
    """Register root options shared by the default app profile."""

    @app.callback()
    def root(
        mode: Annotated[
            CliMode,
            typer.Option("--mode", case_sensitive=False, help="CLI profile."),
        ] = CliMode.CLI,
        yes: Annotated[
            bool,
            typer.Option("--yes", help="Confirm profile prompts."),
        ] = False,
    ) -> None:
        del mode, yes


def apply_agentseek_agent_command_layout(app: typer.Typer, framework) -> None:
    """Mount the opt-in agent profile."""
    app.suggest_commands = False
    _clear_cli_surface(app)

    @app.callback(invoke_without_command=True)
    def agent_root(
        ctx: typer.Context,
        mode: Annotated[
            CliMode,
            typer.Option("--mode", case_sensitive=False, help="CLI profile."),
        ] = CliMode.AGENT,
        yes: Annotated[
            bool,
            typer.Option("--yes", help="Confirm profile prompts."),
        ] = False,
    ) -> None:
        if mode is not CliMode.AGENT:
            return
        _confirm_agent_mode(yes=yes)
        ctx.obj = framework
        if ctx.invoked_subcommand is None:
            from agentseek.cli.banner import format_agentseek_banner

            typer.echo(format_agentseek_banner(agentseek_version()))
            chat.chat(ctx)


def _confirm_agent_mode(*, yes: bool) -> None:
    if yes:
        return
    confirmed = typer.confirm(
        "Enter AgentSeek agent mode?",
        default=False,
    )
    if not confirmed:
        raise typer.Exit(1)


__all__ = [
    "AGENTSEEK_AGENT_MODE_HELP",
    "AGENTSEEK_CLI_HELP",
    "CliMode",
    "agentseek_version",
    "apply_agentseek_agent_command_layout",
    "apply_agentseek_runtime_command_layout",
    "register_app_profile_options",
    "resolve_cli_mode",
]
