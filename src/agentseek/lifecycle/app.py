"""Project lifecycle command groups for the unified ``agentseek`` CLI."""

from __future__ import annotations

from dataclasses import dataclass

import typer

from agentseek.lifecycle.commands import api, build, ctx, deploy, dev, new, skills

LIFECYCLE_HELP = (
    "AgentSeek is a database-native agent harness with one CLI entry point. "
    "Use `agentseek new/dev/build/deploy` to manage projects, "
    "`agentseek chat/turn/gateway` to run the harness, and "
    "`agentseek plugin/ctx/skills/api` to extend the runtime and connect services."
)


@dataclass(frozen=True)
class CommandGroup:
    """A public top-level command group owned by AgentSeek."""

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


def iter_command_groups() -> tuple[CommandGroup, ...]:
    """Return lifecycle groups in the order users see in ``agentseek --help``."""
    return COMMAND_GROUPS


def _registered_names(app: typer.Typer) -> set[str]:
    names = {group.name for group in app.registered_groups if group.name}
    for command in app.registered_commands:
        if command.name:
            names.add(command.name)
        elif command.callback is not None:
            names.add(command.callback.__name__)
    return names


def mount_lifecycle_commands(app: typer.Typer) -> None:
    """Mount project lifecycle and service bridge commands onto ``app``."""
    registered = _registered_names(app)
    for group in iter_command_groups():
        if group.name in registered:
            continue
        app.add_typer(group.app, name=group.name, rich_help_panel=group.panel)
        registered.add(group.name)


__all__ = [
    "COMMAND_GROUPS",
    "LIFECYCLE_HELP",
    "CommandGroup",
    "iter_command_groups",
    "mount_lifecycle_commands",
]
