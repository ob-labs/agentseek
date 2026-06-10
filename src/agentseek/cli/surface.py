"""Public command surface for the unified ``agentseek`` CLI."""

from __future__ import annotations

from dataclasses import dataclass

import typer

from agentseek.cli.commands import api, build, ctx, deploy, dev, new, skills

AGENTSEEK_CLI_HELP = (
    "AgentSeek is a database-native agent harness with one CLI entry point. "
    "Use `agentseek new/dev/build/deploy` to manage projects, "
    "`agentseek chat/turn/gateway` to run the harness, and "
    "`agentseek plugin/ctx/skills/api` to extend the runtime and connect services."
)


@dataclass(frozen=True)
class CommandCapability:
    """A public top-level CLI capability owned by AgentSeek."""

    name: str
    panel: str
    summary: str
    app: typer.Typer


COMMAND_CAPABILITIES: tuple[CommandCapability, ...] = (
    CommandCapability("new", "Project", "Create a project from an AgentSeek template.", new.app),
    CommandCapability("dev", "Project", "Run the current project locally.", dev.app),
    CommandCapability("build", "Project", "Build the current project into a deployable image.", build.app),
    CommandCapability("deploy", "Project", "Render deployment manifests for the current project.", deploy.app),
    CommandCapability("api", "Services", "Forward service commands to agentseek-api.", api.app),
    CommandCapability("ctx", "Services", "Forward context commands to ContextSeek.", ctx.app),
    CommandCapability("skills", "Services", "Manage skills through the configured skill CLI.", skills.app),
)


def iter_command_capabilities() -> tuple[CommandCapability, ...]:
    """Return command capabilities in the order users see in ``agentseek --help``."""
    return COMMAND_CAPABILITIES


def _registered_names(app: typer.Typer) -> set[str]:
    names = {group.name for group in app.registered_groups if group.name}
    for command in app.registered_commands:
        if command.name:
            names.add(command.name)
        elif command.callback is not None:
            cb_name = getattr(command.callback, "__name__", None)
            if cb_name is not None:
                names.add(cb_name)
    return names


def mount_agentseek_commands(app: typer.Typer) -> None:
    """Mount AgentSeek-owned commands onto ``app`` without shadowing framework commands."""
    registered = _registered_names(app)
    for group in iter_command_capabilities():
        if group.name in registered:
            continue
        app.add_typer(group.app, name=group.name, rich_help_panel=group.panel)
        registered.add(group.name)


__all__ = [
    "AGENTSEEK_CLI_HELP",
    "COMMAND_CAPABILITIES",
    "CommandCapability",
    "iter_command_capabilities",
    "mount_agentseek_commands",
]
