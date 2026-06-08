"""Bub plugin that mounts the AgentSeek CLI surface onto the main framework app.

When the main ``agentseek`` package's CLI bootstraps Bub and loads plugins,
``register_cli_commands`` is called with the root Typer app. We attach every
top-level group from :func:`agentseek_cli.app.iter_command_groups`.

Names listed in :data:`CLI_OVERRIDE_NAMES` will **replace** any same-named
command already registered by the framework (e.g. Bub's built-in ``run``
which dispatches a single message is replaced by the CLI's ``run`` which
starts project services locally).

Other groups skip registration if the name is already present (idempotent).

Commands are organized into rich_help_panel groups so ``--help`` shows a
categorized view instead of a flat list.
"""

from __future__ import annotations

import typer
from bub import hookimpl

from agentseek_cli.app import COMMAND_PANELS, iter_command_groups, register_version_command

# Names where agentseek-cli intentionally overrides the framework's built-in
# command. When ``run`` is encountered, we remove the existing registration
# and mount our own.
CLI_OVERRIDE_NAMES: frozenset[str] = frozenset({"run"})

# Panels for Bub's built-in commands (not owned by agentseek-cli).
BUB_COMMAND_PANELS: dict[str, str] = {
    "chat": "Runtime",
    "gateway": "Runtime",
    "install": "Environment",
    "uninstall": "Environment",
    "update": "Environment",
    "onboard": "Environment",
    "login": "Environment",
}


class AgentSeekCliPlugin:
    @hookimpl(trylast=True)
    def register_cli_commands(self, app: typer.Typer) -> None:
        registered = {group.name for group in app.registered_groups}
        for sub in iter_command_groups():
            name = sub.info.name
            if name in CLI_OVERRIDE_NAMES and name in registered:
                app.registered_groups[:] = [g for g in app.registered_groups if g.name != name]
                app.registered_commands[:] = [c for c in app.registered_commands if getattr(c, "name", None) != name]
                registered.discard(name)
            if name in registered:
                continue
            panel = COMMAND_PANELS.get(name)
            app.add_typer(sub, name=name, rich_help_panel=panel)
            registered.add(name)

        # Tag Bub's existing commands with their panels.
        for group in app.registered_groups:
            name = getattr(group, "name", None) or (group.typer_instance.info.name if group.typer_instance else None)
            if name and name in BUB_COMMAND_PANELS and group.typer_instance:
                group.typer_instance.info.rich_help_panel = BUB_COMMAND_PANELS[name]

        for cmd in app.registered_commands:
            name: str | None = getattr(cmd, "name", None)
            if not name and cmd.callback:
                name = getattr(cmd.callback, "__name__", None)
            if name and name in BUB_COMMAND_PANELS:
                cmd.rich_help_panel = BUB_COMMAND_PANELS[name]

        register_version_command(app)


main = AgentSeekCliPlugin()

__all__ = ["BUB_COMMAND_PANELS", "CLI_OVERRIDE_NAMES", "AgentSeekCliPlugin", "main"]
