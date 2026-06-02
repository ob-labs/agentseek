"""``agentseek build`` — package the project into a container image.

Wraps ``docker build`` (or ``docker buildx build`` for multi-platform) with
sensible defaults inferred from the user's project working directory:

* image tag defaults to ``<cwd-slug>:latest``;
* Dockerfile defaults to ``./Dockerfile`` and is required to exist;
* additional ``--build-arg`` flags are forwarded verbatim;
* ``--push`` runs ``docker push <tag>`` after a successful build;
* ``--dry-run`` prints the resolved command(s) without invoking docker.

Command construction (``_build_command``) is split from execution (``_run``)
so the test suite can assert on the rendered argv without spawning docker.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, NoReturn

import typer

app = typer.Typer(
    name="build",
    help="Build the project into a container image (wraps `docker build` / `docker buildx build`).",
    add_completion=False,
    no_args_is_help=False,
)


# --- Tag / Dockerfile resolution ------------------------------------------------


def _slugify(name: str) -> str:
    """Lowercase, replace ``_``/whitespace with ``-``, collapse runs, strip edges."""
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in name.strip())
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "agentseek-project"


def _resolve_tag(cwd: Path, override: str | None) -> str:
    if override is not None:
        return override
    return f"{_slugify(cwd.name)}:latest"


def _resolve_dockerfile(cwd: Path, override: Path | None) -> Path:
    candidate = override if override is not None else cwd / "Dockerfile"
    if not candidate.is_file():
        _raise_missing_dockerfile(candidate)
    return candidate


def _raise_missing_dockerfile(path: Path) -> NoReturn:
    typer.echo(
        f"Dockerfile not found at {path}.\n"
        "Run `agentseek create` to scaffold a project with a Dockerfile, or pass `--file <path>`.",
        err=True,
    )
    raise typer.Exit(2)


# --- Docker / buildx availability ----------------------------------------------


def _ensure_docker() -> None:
    if shutil.which("docker") is None:
        _raise_missing_docker()


def _raise_missing_docker() -> NoReturn:
    typer.echo(
        "`docker` was not found on PATH.\n"
        "Install Docker Desktop or Docker Engine (https://docs.docker.com/get-docker/) and retry.",
        err=True,
    )
    raise typer.Exit(1)


def _ensure_buildx() -> None:
    completed = subprocess.run(
        ["docker", "buildx", "version"],  # noqa: S607
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        _raise_missing_buildx()


def _raise_missing_buildx() -> NoReturn:
    typer.echo(
        "`docker buildx` is not available but is required for multi-platform builds.\n"
        "Enable Buildx (https://docs.docker.com/buildx/working-with-buildx/) and retry.",
        err=True,
    )
    raise typer.Exit(1)


# --- Command construction ------------------------------------------------------


def _split_platforms(value: str | None) -> list[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


def _build_command(
    *,
    tag: str,
    dockerfile: Path,
    context: Path,
    platforms: Sequence[str],
    no_cache: bool,
    build_args: Sequence[str],
) -> list[str]:
    """Return the argv for ``docker [buildx] build``.

    Multi-platform invocations (``len(platforms) > 1``) switch to
    ``docker buildx build`` because plain ``docker build`` cannot honor a
    comma-separated ``--platform`` value.
    """
    use_buildx = len(platforms) > 1
    cmd: list[str] = ["docker", "buildx", "build"] if use_buildx else ["docker", "build"]
    cmd.extend(["-t", tag, "-f", str(dockerfile)])
    if no_cache:
        cmd.append("--no-cache")
    if platforms:
        cmd.extend(["--platform", ",".join(platforms)])
    for arg in build_args:
        cmd.extend(["--build-arg", arg])
    cmd.append(str(context))
    return cmd


def _push_command(tag: str) -> list[str]:
    return ["docker", "push", tag]


# --- Execution ----------------------------------------------------------------


def _run(cmd: Sequence[str], *, dry_run: bool) -> int:
    if dry_run:
        typer.echo(" ".join(cmd))
        return 0
    completed = subprocess.run(list(cmd), check=False)  # noqa: S603
    return completed.returncode


# --- CLI ----------------------------------------------------------------------


@app.callback(invoke_without_command=True)
def build(
    tag: Annotated[
        str | None,
        typer.Option(
            "--tag",
            "-t",
            help="Image tag, e.g. `myproj:1.0`. Defaults to `<cwd-slug>:latest`.",
            show_default=False,
        ),
    ] = None,
    file: Annotated[
        Path | None,
        typer.Option(
            "--file",
            "-f",
            help="Path to the Dockerfile.",
            show_default=False,
        ),
    ] = None,
    context: Annotated[
        Path,
        typer.Option(
            "--context",
            help="Build context directory.",
        ),
    ] = Path("."),
    platform: Annotated[
        str | None,
        typer.Option(
            "--platform",
            help="Comma-separated target platforms, e.g. `linux/amd64,linux/arm64`.",
            show_default=False,
        ),
    ] = None,
    push: Annotated[
        bool,
        typer.Option("--push", help="Push the image after a successful build."),
    ] = False,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Do not use cache when building."),
    ] = False,
    build_arg: Annotated[
        list[str] | None,
        typer.Option(
            "--build-arg",
            help="Pass build-time variable. Use `KEY=VALUE`. May be repeated.",
            show_default=False,
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Print the resolved command(s) without executing them."),
    ] = False,
) -> None:
    cwd = Path.cwd()
    resolved_tag = _resolve_tag(cwd, tag)
    resolved_dockerfile = _resolve_dockerfile(cwd, file).resolve()
    resolved_context = context.resolve()
    platforms = _split_platforms(platform)
    args = list(build_arg or [])

    if not dry_run:
        _ensure_docker()
        if len(platforms) > 1:
            _ensure_buildx()

    cmd = _build_command(
        tag=resolved_tag,
        dockerfile=resolved_dockerfile,
        context=resolved_context,
        platforms=platforms,
        no_cache=no_cache,
        build_args=args,
    )
    rc = _run(cmd, dry_run=dry_run)
    if rc != 0:
        raise typer.Exit(rc)

    if push:
        rc = _run(_push_command(resolved_tag), dry_run=dry_run)
        if rc != 0:
            raise typer.Exit(rc)


__all__ = [
    "_build_command",
    "_push_command",
    "_resolve_dockerfile",
    "_resolve_tag",
    "_slugify",
    "app",
]
