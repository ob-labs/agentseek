"""CLI wrapper for bubseek distribution management."""

# ruff: noqa: B008
from __future__ import annotations

import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import typer
from typer.main import get_command

from bubseek.config import generate_config, generate_lock
from bubseek.sync import SyncResult, sync_from_lock

GenerateConfig = Callable[..., Path]
GenerateLock = Callable[..., Path]
SyncFromLock = Callable[..., SyncResult]
ForwardCommand = Callable[[list[str]], int]
Echo = Callable[[str], None]
MANAGEMENT_COMMANDS = {"init", "lock", "sync", "help", "-h", "--help"}


@dataclass(frozen=True)
class BubseekCliDependencies:
    generate_config: GenerateConfig
    generate_lock: GenerateLock
    sync_from_lock: SyncFromLock
    forward_command: ForwardCommand
    echo: Echo


def create_cli_app(dependencies: BubseekCliDependencies | None = None) -> typer.Typer:
    resolved_dependencies = dependencies or _default_dependencies()
    cli = typer.Typer(
        name="bubseek",
        help="Bubseek distribution management commands. Other commands are forwarded to bub.",
        add_completion=False,
        no_args_is_help=True,
    )

    @cli.callback()
    def _main(ctx: typer.Context) -> None:
        ctx.obj = resolved_dependencies

    @cli.command("init")
    def init_command(
        ctx: typer.Context,
        config: Path | None = typer.Option(None, "--config", help="Path to bubseek.toml"),
        force: bool = typer.Option(False, "--force", help="Overwrite existing config file"),
        project_name: str = typer.Option("bubseek", "--project-name", help="Project name in config"),
        version: str = typer.Option("0.1.0", "--version", help="Project version in config"),
        contrib: list[str] = typer.Option([], "--contrib", help="Contrib package name. Repeat for multiple packages."),
        contrib_repo: str = typer.Option(
            "https://github.com/bubbuild/bub-contrib",
            "--contrib-repo",
            help="Contrib repository URL",
        ),
        with_lock: bool = typer.Option(False, "--with-lock", help="Generate lock after config"),
    ) -> None:
        deps = ctx.ensure_object(BubseekCliDependencies)
        config_path = deps.generate_config(
            config_path=config,
            overwrite=force,
            project_name=project_name,
            version=version,
            contrib_packages=contrib or None,
            contrib_repo_url=contrib_repo,
        )
        deps.echo(f"generated config: {config_path}")
        if with_lock:
            lock_path = deps.generate_lock(config_path=config_path)
            deps.echo(f"generated lock: {lock_path}")

    @cli.command("lock")
    def lock_command(
        ctx: typer.Context,
        config: Path | None = typer.Option(None, "--config", help="Path to bubseek.toml"),
        lock: Path | None = typer.Option(None, "--lock", help="Path to output lock file"),
    ) -> None:
        deps = ctx.ensure_object(BubseekCliDependencies)
        lock_path = deps.generate_lock(config_path=config, lock_path=lock)
        deps.echo(f"generated lock: {lock_path}")

    @cli.command("sync")
    def sync_command(
        ctx: typer.Context,
        config: Path | None = typer.Option(None, "--config", help="Path to bubseek.toml"),
        lock: Path | None = typer.Option(None, "--lock", help="Path to bubseek.lock"),
        workspace: Path = typer.Option(Path.cwd(), "--workspace", "-w", help="Target workspace path"),
        no_contrib: bool = typer.Option(False, "--no-contrib", help="Skip contrib installation"),
        no_skills: bool = typer.Option(False, "--no-skills", help="Skip skills synchronization"),
        overwrite_skills: bool = typer.Option(False, "--overwrite-skills", help="Overwrite existing workspace skills"),
    ) -> None:
        deps = ctx.ensure_object(BubseekCliDependencies)
        result = deps.sync_from_lock(
            config_path=config,
            lock_path=lock,
            workspace=workspace,
            sync_contrib=not no_contrib,
            sync_skills=not no_skills,
            overwrite_skills=overwrite_skills,
        )
        _echo_sync_result(result, echo=deps.echo)

    return cli


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if _should_forward(args):
        return _default_dependencies().forward_command(args)
    command = get_command(app)
    result = command.main(args=args, prog_name="bubseek", standalone_mode=False)
    return int(result) if isinstance(result, int) else 0


def _echo_sync_result(result: SyncResult, *, echo: Echo) -> None:
    if result.installed_bub is not None:
        echo(f"bub: {result.installed_bub}")
    for name in result.installed_contrib:
        echo(f"contrib: {name}")
    for path in result.installed_skills:
        echo(f"skill: {path}")
    for name in result.skipped_skills:
        echo(f"skill(skip): {name}")
    if not result.installed_contrib and not result.installed_skills and not result.skipped_skills:
        echo("(nothing to sync)")


def _default_dependencies() -> BubseekCliDependencies:
    return BubseekCliDependencies(
        generate_config=generate_config,
        generate_lock=generate_lock,
        sync_from_lock=sync_from_lock,
        forward_command=_forward_to_bub,
        echo=typer.echo,
    )


def _should_forward(args: list[str]) -> bool:
    return bool(args) and args[0] not in MANAGEMENT_COMMANDS


def _forward_to_bub(args: list[str]) -> int:
    executable = shutil.which("bub")
    if executable is None:
        raise FileNotFoundError("command not found: bub")
    completed = subprocess.run([executable, *args], check=False)
    return int(completed.returncode)


app = create_cli_app()


if __name__ == "__main__":
    raise SystemExit(main())
