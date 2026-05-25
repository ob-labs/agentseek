"""``agentseek build`` — package the project into a container image.

Surface-only in v1.
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="build",
    help="Build the project into a container image.",
    add_completion=False,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def build() -> None:
    typer.echo("agentseek build — coming soon.")


__all__ = ["app"]
