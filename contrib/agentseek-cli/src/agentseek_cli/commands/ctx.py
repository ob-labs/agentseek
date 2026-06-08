"""``agentseek ctx`` — thin forwarder around the upstream ``contextseek`` CLI.

Design notes
------------

This module deliberately does **not** enumerate the contextseek subcommands
(``add``, ``retrieve``, ``compact``, …) or maintain any DataPlug class map.
Whatever ``contextseek`` exposes is what ``agentseek ctx`` exposes; if upstream
adds, renames, or removes a verb we get it for free with no edit here.

Implementation: a tiny Click ``Group`` subclass routes any unknown
sub-command to ``contextseek.cli.main:run_cli``. There are no locally-owned
sub-commands. Project scaffolding (``.env`` snippets, MCP server registration)
is intentionally **not** handled here — it belongs to the
``agentseek-contextseek`` plugin's installation guidance.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import NoReturn

import click
import typer
from typer.core import TyperGroup

# Signature of ``contextseek.cli.run_cli`` we forward to.
_RunCli = Callable[[Sequence[str]], int]


class _ContextSeekForwardingGroup(TyperGroup):
    """Group that forwards any sub-command (and ``--help``) to contextseek.

    The group is configured with ``add_help_option=False`` and
    ``help_option_names=[]`` so the root parser never claims ``--help`` for
    itself; together with the open ``get_command`` below, that means every
    token (including ``--help``) flows through to ``contextseek.cli.run_cli``.
    """

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        return _build_forward_command(cmd_name)

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        if not args:
            args = ["--help"]
        cmd = _build_forward_command(args[0])
        return args[0], cmd, args[1:]


def _build_forward_command(name: str) -> click.Command:
    """Create a one-shot Click command that forwards ``[name, *extra]`` upstream."""

    @click.command(
        name=name,
        add_help_option=False,
        context_settings={
            "allow_extra_args": True,
            "ignore_unknown_options": True,
            "help_option_names": [],
        },
    )
    @click.pass_context
    def _forward(click_ctx: click.Context) -> None:
        _forward_to_contextseek([name, *click_ctx.args])

    return _forward


app = typer.Typer(
    name="ctx",
    help="ContextSeek — semantic context layer (forwarded to the `contextseek` CLI).",
    add_completion=False,
    cls=_ContextSeekForwardingGroup,
    context_settings={
        "help_option_names": [],
        "ignore_unknown_options": True,
        "allow_extra_args": True,
    },
    invoke_without_command=True,
)


@app.callback()
def _ctx_root(typer_ctx: typer.Context) -> None:
    """Forward ``agentseek ctx`` (no args) to the upstream ``--help``."""
    if typer_ctx.invoked_subcommand is None:
        _forward_to_contextseek(["--help"])


def _forward_to_contextseek(argv: Sequence[str]) -> None:
    run_cli = _load_contextseek_run_cli()
    exit_code = run_cli(list(argv))
    raise typer.Exit(exit_code)


def _load_contextseek_run_cli() -> _RunCli:
    try:
        from contextseek.cli import run_cli
    except ModuleNotFoundError as exc:
        if exc.name and not exc.name.startswith("contextseek"):
            raise
        _raise_missing_contextseek()
    if not callable(run_cli):
        _raise_invalid_contextseek()
    return run_cli


def _raise_missing_contextseek() -> NoReturn:
    typer.echo(
        "The `agentseek ctx` commands require `agentseek-contextseek` in the current environment.\n"
        "Install it with:  agentseek plugin install agentseek-contextseek",
        err=True,
    )
    raise typer.Exit(1)


def _raise_invalid_contextseek() -> NoReturn:
    typer.echo(
        "The installed `contextseek` package does not expose the expected CLI entrypoint.",
        err=True,
    )
    raise typer.Exit(1)


__all__ = ["app"]
