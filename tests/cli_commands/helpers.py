from __future__ import annotations

import typer

from agentseek.cli.surface import mount_agentseek_commands


def build_command_app() -> typer.Typer:
    app = typer.Typer(name="agentseek", add_completion=False, suggest_commands=False)
    mount_agentseek_commands(app)
    return app
