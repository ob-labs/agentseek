from __future__ import annotations

import typer

from agentseek.lifecycle.app import mount_lifecycle_commands


def build_lifecycle_app() -> typer.Typer:
    app = typer.Typer(name="agentseek", add_completion=False, suggest_commands=False)
    mount_lifecycle_commands(app)
    return app
