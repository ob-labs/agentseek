"""``agentseek deploy`` — generate deployment manifests for the project.

Surface-only in v1 — flags are validated so future automation can drop in
without churning the documented surface.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

import typer


class DeployMode(StrEnum):
    DOCKER_COMPOSE = "docker-compose"
    K8S = "k8s"
    BOTH = "both"


app = typer.Typer(
    name="deploy",
    help="Generate deployment manifests (docker-compose / k8s).",
    add_completion=False,
    no_args_is_help=False,
)


@app.callback(invoke_without_command=True)
def deploy(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Generate manifest files without performing an actual deployment."),
    ] = False,
    mode: Annotated[
        DeployMode,
        typer.Option("--mode", case_sensitive=False, help="Deployment target: docker-compose | k8s | both."),
    ] = DeployMode.BOTH,
) -> None:
    if not dry_run:
        typer.echo(
            "Only --dry-run is supported in v1. Re-run with --dry-run to generate manifests.",
            err=True,
        )
        raise typer.Exit(2)
    typer.echo(f"agentseek deploy --dry-run --mode {mode.value} — coming soon (manifest generation).")


__all__ = ["DeployMode", "app"]
