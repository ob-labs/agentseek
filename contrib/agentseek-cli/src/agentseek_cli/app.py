"""Single source of truth for the AgentSeek CLI surface.

``build_app()`` returns a fresh ``typer.Typer`` with every documented top-level
group attached. The standalone console script and the Bub plugin both go
through this function so the two entry shapes stay in sync.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

import typer

from agentseek_cli.commands import api, build, ctx, deploy, dev, new, skills

CLI_HELP = "AgentSeek CLI. Scaffold, develop, build, deploy, manage API services, skills, and context."
VERSION_COMMAND_NAME = "version"


def _get_package_version(package_name: str) -> str | None:
    with contextlib.suppress(PackageNotFoundError):
        return package_version(package_name)
    return None


def _get_version_string() -> str:
    cli_version = _get_package_version("agentseek-cli") or "(unknown)"
    parts = [f"agentseek-cli {cli_version}"]
    if agentseek_version := _get_package_version("agentseek"):
        parts.append(f"agentseek {agentseek_version}")
    return "\n".join(parts)


@dataclass(frozen=True)
class CommandGroup:
    """A public top-level command group owned by the project lifecycle CLI."""

    name: str
    app: typer.Typer
    panel: str


COMMAND_GROUPS: tuple[CommandGroup, ...] = (
    CommandGroup("new", new.app, "Project"),
    CommandGroup("dev", dev.app, "Project"),
    CommandGroup("build", build.app, "Project"),
    CommandGroup("deploy", deploy.app, "Project"),
    CommandGroup("api", api.app, "Services"),
    CommandGroup("ctx", ctx.app, "Services"),
    CommandGroup("skills", skills.app, "Services"),
)
COMMAND_PANELS: dict[str, str] = {group.name: group.panel for group in COMMAND_GROUPS}


def iter_command_groups() -> tuple[CommandGroup, ...]:
    """Return the top-level Typer groups that make up the AgentSeek CLI.

    The order here is the order users see in ``agentseek --help``.
    """
    return COMMAND_GROUPS


def register_version_command(app: typer.Typer) -> None:
    """Add ``agentseek version`` to the given app."""
    if any(getattr(command, "name", None) == VERSION_COMMAND_NAME for command in app.registered_commands):
        return

    @app.command(VERSION_COMMAND_NAME, rich_help_panel="Environment")
    def version_cmd() -> None:
        """Show version information."""
        typer.echo(_get_version_string())


def build_app() -> typer.Typer:
    """Build a fresh standalone Typer app named ``agentseek``."""
    app = typer.Typer(
        name="agentseek",
        help=CLI_HELP,
        add_completion=False,
        no_args_is_help=True,
    )
    for group in iter_command_groups():
        app.add_typer(group.app, name=group.name, rich_help_panel=group.panel)
    register_version_command(app)
    return app


__all__ = ["CLI_HELP", "CommandGroup", "build_app", "iter_command_groups", "register_version_command"]
