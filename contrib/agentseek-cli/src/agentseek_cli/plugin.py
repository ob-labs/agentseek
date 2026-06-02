"""Bub plugin that mounts the AgentSeek CLI surface onto the main framework app.

When the main ``agentseek`` package's CLI bootstraps Bub and loads plugins,
``register_cli_commands`` is called with the root Typer app. We attach every
top-level group from :func:`agentseek_cli.app.iter_command_groups`.

Names listed in :data:`CLI_OVERRIDE_NAMES` will **replace** any same-named
command already registered by the framework (e.g. Bub's built-in ``run``
which dispatches a single message is replaced by the CLI's ``run`` which
starts project services locally).

Other groups skip registration if the name is already present (idempotent).
"""

from __future__ import annotations

import typer
from bub import hookimpl

from agentseek_cli.app import iter_command_groups

# Names where agentseek-cli intentionally overrides the framework's built-in
# command. When ``run`` is encountered, we remove the existing registration
# and mount our own.
CLI_OVERRIDE_NAMES: frozenset[str] = frozenset({"run"})


class AgentSeekCliPlugin:
    @hookimpl
    def register_cli_commands(self, app: typer.Typer) -> None:
        registered = {group.name for group in app.registered_groups}
        for sub in iter_command_groups():
            name = sub.info.name
            if name in CLI_OVERRIDE_NAMES and name in registered:
                # Remove the existing command/group so ours takes precedence.
                app.registered_groups[:] = [g for g in app.registered_groups if g.name != name]
                app.registered_commands[:] = [c for c in app.registered_commands if getattr(c, "name", None) != name]
                registered.discard(name)
            if name in registered:
                continue
            app.add_typer(sub, name=name)
            registered.add(name)


main = AgentSeekCliPlugin()

__all__ = ["CLI_OVERRIDE_NAMES", "AgentSeekCliPlugin", "main"]
