"""Bub plugin that mounts the AgentSeek CLI surface onto the main framework app.

When the main ``agentseek`` package's CLI bootstraps Bub and loads plugins,
``register_cli_commands`` is called with the root Typer app. We attach every
top-level group from :func:`agentseek_cli.app.iter_command_groups`, skipping:

* any group already present (idempotent re-registration); and
* names in :data:`FRAMEWORK_OWNED_NAMES` that the main ``agentseek`` framework
  already provides through Bub's built-in plugins. Typer's ``add_typer``
  silently overwrites on duplicate names, so without this skip our stub
  groups would shadow first-class framework commands like ``run``.
"""

from __future__ import annotations

import typer
from bub import hookimpl

from agentseek_cli.app import iter_command_groups

# Names owned by the main `agentseek` framework's built-in plugins. We never
# mount these as our own when running as a Bub plugin — the standalone uvx
# entrypoint still exposes them via `agentseek_cli.app.build_app()`.
FRAMEWORK_OWNED_NAMES: frozenset[str] = frozenset({"run"})


class AgentSeekCliPlugin:
    @hookimpl
    def register_cli_commands(self, app: typer.Typer) -> None:
        registered = {group.name for group in app.registered_groups}
        for sub in iter_command_groups():
            name = sub.info.name
            if name in registered or name in FRAMEWORK_OWNED_NAMES:
                continue
            app.add_typer(sub, name=name)
            registered.add(name)


main = AgentSeekCliPlugin()

__all__ = ["FRAMEWORK_OWNED_NAMES", "AgentSeekCliPlugin", "main"]
