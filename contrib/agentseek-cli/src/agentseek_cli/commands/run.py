"""``agentseek run`` — run the project locally and open the frontend.

Surface-only in v1.
"""

from __future__ import annotations

import typer

app = typer.Typer(
    name="run",
    help="Run the project locally after completing .env configuration.",
    add_completion=False,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def run() -> None:
    typer.echo("agentseek run — coming soon.")


__all__ = ["app"]
