from __future__ import annotations

import typer

from agentseek.cli import apply_agentseek_runtime_command_layout


def build_command_app() -> typer.Typer:
    app = typer.Typer(name="agentseek", add_completion=False)
    apply_agentseek_runtime_command_layout(app)
    return app
