"""``agentseek api`` — passthrough to the optional ``agentseek-api`` package.

Originally lived in ``agentseek-langchain``; migrated here because the
``api`` group is framework-agnostic. When ``agentseek-api`` is not installed
we exit with a clear instruction to install it.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import NoReturn, Protocol, runtime_checkable

import typer

API_COMMANDS: tuple[str, ...] = ("dev", "serve", "dockerfile", "build", "up", "version")

_PASSTHROUGH_CONTEXT_SETTINGS = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "help_option_names": [],
}

app = typer.Typer(
    name="api",
    help="Forward API runtime commands to `agentseek-api` when it is installed.",
    add_completion=False,
    no_args_is_help=True,
)


@runtime_checkable
class AgentSeekApiCliModule(Protocol):
    def main(
        self,
        argv: Sequence[str] | None = None,
        *,
        prog: str | None = None,
        cwd: str | Path | None = None,
    ) -> int: ...


def _load_agentseek_api_cli() -> AgentSeekApiCliModule:
    try:
        module = importlib.import_module("agentseek_api.cli")
    except ModuleNotFoundError as exc:
        if not _is_missing_agentseek_api_module(exc):
            raise
        _raise_missing_agentseek_api_dependency()
    if not isinstance(module, AgentSeekApiCliModule):
        _raise_invalid_agentseek_api_dependency()
    return module


def _forward_to_agentseek_api(command_name: str, raw_args: list[str]) -> None:
    cli_module = _load_agentseek_api_cli()
    exit_code = cli_module.main(
        [command_name, *raw_args],
        prog="agentseek api",
        cwd=Path.cwd(),
    )
    raise typer.Exit(exit_code)


def _passthrough_command(command_name: str) -> Callable[[typer.Context], None]:
    def command(ctx: typer.Context) -> None:
        _forward_to_agentseek_api(command_name, list(ctx.args))

    command.__name__ = f"api_{command_name}"
    command.__doc__ = f"Forward `{command_name}` to `agentseek-api`."
    return command


for _command_name in API_COMMANDS:
    app.command(_command_name, context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)(_passthrough_command(_command_name))


def _is_missing_agentseek_api_module(exc: ModuleNotFoundError) -> bool:
    missing_name = getattr(exc, "name", None) or (str(exc.args[0]) if exc.args else None)
    return missing_name in {"agentseek_api", "agentseek_api.cli"}


def _raise_missing_agentseek_api_dependency() -> NoReturn:
    typer.echo(
        "The `agentseek api` commands require `agentseek-api` in the current environment.\n"
        "Install it first, for example: `uv pip install -e references/agentseek-api`.",
        err=True,
    )
    raise typer.Exit(1)


def _raise_invalid_agentseek_api_dependency() -> NoReturn:
    typer.echo(
        "The installed `agentseek-api` package does not expose the expected CLI entrypoint.",
        err=True,
    )
    raise typer.Exit(1)


__all__ = ["API_COMMANDS", "AgentSeekApiCliModule", "app"]
