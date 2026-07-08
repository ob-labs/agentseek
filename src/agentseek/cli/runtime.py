"""AgentSeek CLI runtime profiles."""

from __future__ import annotations

from enum import StrEnum
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version
from typing import Annotated

import typer

from agentseek.cli.commands import chat, create, dev, doctor, info, task

AGENTSEEK_CLI_HELP = "AgentSeek is the Toolkit for App Development Lifecycle."
AGENTSEEK_AGENT_MODE_HELP = f"{AGENTSEEK_CLI_HELP}\n\nAgent mode is experimental and requires explicit confirmation."

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
        raise SystemExit(2) from None


def _clear_cli_surface(app: typer.Typer) -> None:
    app.registered_commands.clear()
    app.registered_groups.clear()


def apply_agentseek_runtime_command_layout(app: typer.Typer) -> None:
    """Mount the default app lifecycle command surface."""
    app.suggest_commands = False
    _clear_cli_surface(app)

    app.add_typer(create.app, name="create", rich_help_panel=PROJECT_COMMAND_PANEL)
    app.command(
        "dev", rich_help_panel=PROJECT_COMMAND_PANEL, help="Run the current project locally through the lifecycle spec."
    )(dev.dev)
    app.command("info", rich_help_panel=PROJECT_COMMAND_PANEL, help="Show a project summary from the lifecycle spec.")(
        info.info
    )
    app.command(
        "doctor",
        rich_help_panel=PROJECT_COMMAND_PANEL,
        help="Check local project readiness through the lifecycle spec.",
    )(doctor.doctor)
    app.command(
        "task",
        rich_help_panel=PROJECT_COMMAND_PANEL,
        context_settings={"allow_extra_args": True, "ignore_unknown_options": True, "help_option_names": []},
        help="Run project lifecycle spec tasks.",
    )(task.task)


def register_app_profile_options(app: typer.Typer) -> None:
    """Register root options shared by the default app profile."""

    @app.callback()
    def root(
        mode: Annotated[
            CliMode,
            typer.Option("--mode", case_sensitive=False, help="CLI profile."),
        ] = CliMode.CLI,
    ) -> None:
        del mode


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
    ) -> None:
        if mode is not CliMode.AGENT:
            return
        _confirm_agent_mode()
        ctx.obj = framework
        if ctx.invoked_subcommand is None:
            from agentseek.cli.banner import format_agentseek_banner

            typer.echo(format_agentseek_banner(agentseek_version()))
            chat.chat(ctx)


def _confirm_agent_mode() -> None:
    confirmed = typer.confirm(
        "AgentSeek agent mode is experimental. Enter it?",
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
