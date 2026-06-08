"""Bub plugin that mounts the AgentSeek project command surface.

When the main ``agentseek`` package's CLI bootstraps Bub and loads plugins,
``register_cli_commands`` is called with the root Typer app. We attach the
project lifecycle and bridge groups from :func:`agentseek_cli.app.iter_command_groups`.
Existing root names are treated as owned by the framework and are never
overridden.

Commands are organized into rich_help_panel groups so ``--help`` shows a
categorized view instead of a flat list.
"""

from __future__ import annotations

import typer
from bub import hookimpl

from agentseek_cli.app import iter_command_groups, register_version_command


def _registered_names(app: typer.Typer) -> set[str]:
    names = {group.name for group in app.registered_groups if group.name}
    for command in app.registered_commands:
        if command.name:
            names.add(command.name)
        elif command.callback is not None:
            names.add(command.callback.__name__)
    return names


class AgentSeekCliPlugin:
    @hookimpl(trylast=True)
    def register_cli_commands(self, app: typer.Typer) -> None:
        registered = _registered_names(app)
        for group in iter_command_groups():
            name = group.name
            if name in registered:
                continue
            app.add_typer(group.app, name=name, rich_help_panel=group.panel)
            registered.add(name)

        register_version_command(app)


main = AgentSeekCliPlugin()

__all__ = ["AgentSeekCliPlugin", "main"]
