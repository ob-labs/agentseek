"""``agentseek task`` — forward project lifecycle duties."""

from __future__ import annotations

from pathlib import Path

import typer

from agentseek.cli.lifecycle import LIFECYCLE_FILE, load_lifecycle_project, run_duty_cli


def _is_help_request(args: list[str]) -> bool:
    return bool(args) and args[0] in {"--help", "-h"}


def _print_task_help() -> None:
    typer.echo("Usage: agentseek task [DUTY [DUTY_OPTS...] [DUTY_PARAMS...]]")
    typer.echo()
    typer.echo("Run project-defined tasks from duties.py through Duty's native parser.")
    typer.echo()
    typer.echo("Forms:")
    typer.echo("  agentseek task --list")
    typer.echo("  agentseek task --help [DUTY...]")
    typer.echo("  agentseek task <name>")
    typer.echo("  agentseek task <name> key=value")
    typer.echo()
    typer.echo(f"This command must be run from a project containing {LIFECYCLE_FILE}.")


def task(ctx: typer.Context) -> None:
    """Forward arbitrary duty commands from the current project."""
    args = list(ctx.args)
    if _is_help_request(args) and not (Path.cwd() / LIFECYCLE_FILE).is_file():
        _print_task_help()
        return
    project = load_lifecycle_project()
    code = run_duty_cli(project, args)
    if code:
        raise typer.Exit(code)


__all__ = ["task"]
