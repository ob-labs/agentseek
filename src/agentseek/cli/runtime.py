"""AgentSeek CLI runtime — orchestrates command layout on top of Bub's app.

After ``BubFramework.create_cli_app()`` returns, ``apply_agentseek_runtime_command_layout``
pops Bub's builtin commands and mounts AgentSeek's own implementations from
:mod:`agentseek.cli.commands`.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

import typer

from agentseek.cli.commands import api, build, chat, create, ctx, deploy, onboard, plugin, run, skills
from agentseek.cli.commands.chat import resolve_enabled_channels
from agentseek.cli.commands.onboard import AGENTSEEK_ONBOARD_BANNER, AGENTSEEK_ONBOARD_WELCOME

AGENTSEEK_CLI_HELP = (
    "AgentSeek is a database-native agent harness with one CLI entry point.\n\n"
    "Project lifecycle: `agentseek create → run → build → deploy`.\n"
    "Runtime: `agentseek chat / turn / gateway`.\n"
    "Environment: `agentseek plugin / onboard / mcp / login`.\n"
    "Services: `agentseek api / ctx / skills`."
)

RUNTIME_COMMAND_PANELS: dict[str, str] = {
    "chat": "Runtime",
    "gateway": "Runtime",
    "turn": "Runtime",
    "plugin": "Environment",
    "mcp": "Environment",
    "onboard": "Environment",
    "login": "Environment",
}


def agentseek_version() -> str:
    try:
        return package_version("agentseek")
    except PackageNotFoundError:
        return "0.0.0"


# ---------------------------------------------------------------------------
# Layout — pop Bub commands, mount AgentSeek replacements
# ---------------------------------------------------------------------------


def _command_name(command: typer.models.CommandInfo) -> str | None:
    if command.name:
        return command.name
    if command.callback is None:
        return None
    return getattr(command.callback, "__name__", None)


def _pop_command(app: typer.Typer, name: str) -> typer.models.CommandInfo | None:
    for index, command in enumerate(app.registered_commands):
        if _command_name(command) == name:
            return app.registered_commands.pop(index)
    return None


def _tag_panels(app: typer.Typer) -> None:
    for group in app.registered_groups:
        name = getattr(group, "name", None) or (group.typer_instance.info.name if group.typer_instance else None)
        if name and name in RUNTIME_COMMAND_PANELS and group.typer_instance:
            group.typer_instance.info.rich_help_panel = RUNTIME_COMMAND_PANELS[name]

    for command in app.registered_commands:
        name = _command_name(command)
        if name and name in RUNTIME_COMMAND_PANELS:
            command.rich_help_panel = RUNTIME_COMMAND_PANELS[name]


def apply_agentseek_runtime_command_layout(app: typer.Typer) -> None:
    """Replace Bub builtin commands with AgentSeek implementations and reorganize the layout."""
    app.suggest_commands = False

    # Bub's `run` → `turn` (callback reused unchanged)
    run_cmd = _pop_command(app, "run")
    if run_cmd and run_cmd.callback is not None:
        app.command("turn", rich_help_panel="Runtime")(run_cmd.callback)

    # Replace chat, onboard with AgentSeek implementations
    _pop_command(app, "chat")
    app.command("chat", rich_help_panel="Runtime")(chat.chat)

    _pop_command(app, "onboard")
    app.command("onboard", rich_help_panel="Environment")(onboard.onboard)

    # Group install/uninstall/update under `plugin`
    for name in ("install", "uninstall", "update"):
        _pop_command(app, name)
    if not any(group.name == "plugin" for group in app.registered_groups):
        app.add_typer(plugin.app, name="plugin", rich_help_panel="Environment")

    # Mount AgentSeek project + service commands
    registered = {group.name for group in app.registered_groups if group.name}
    registered.update(c.name for c in app.registered_commands if c.name)
    for name, panel, sub_app in (
        ("create", "Project", create.app),
        ("run", "Project", run.app),
        ("build", "Project", build.app),
        ("deploy", "Project", deploy.app),
        ("api", "Services", api.app),
        ("ctx", "Services", ctx.app),
        ("skills", "Services", skills.app),
    ):
        if name not in registered:
            app.add_typer(sub_app, name=name, rich_help_panel=panel)
            registered.add(name)

    _tag_panels(app)


__all__ = [
    "AGENTSEEK_CLI_HELP",
    "AGENTSEEK_ONBOARD_BANNER",
    "AGENTSEEK_ONBOARD_WELCOME",
    "agentseek_version",
    "apply_agentseek_runtime_command_layout",
    "resolve_enabled_channels",
]
