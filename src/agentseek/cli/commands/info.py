"""``agentseek info`` — print project lifecycle information."""

from __future__ import annotations

from typing import Annotated

import typer

from agentseek.cli.lifecycle import load_lifecycle_project, run_lifecycle_task
from agentseek.cli.lifecycle.json_commands import print_info_json

app = typer.Typer(
    name="info",
    help="Show a project summary from the lifecycle spec.",
    add_completion=False,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def info(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Show discovery details from the lifecycle loader."),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit versioned machine-readable lifecycle metadata."),
    ] = False,
) -> None:
    """Print a copyable project summary."""
    if json_output:
        print_info_json()
        return
    project = load_lifecycle_project()
    if verbose:
        typer.echo(f"Lifecycle spec: {project.path}")
        typer.echo(f"Lifecycle version: {project.metadata['version']}")
        typer.echo()
    run_lifecycle_task(project, "info", verbose=verbose)


__all__ = ["app"]
