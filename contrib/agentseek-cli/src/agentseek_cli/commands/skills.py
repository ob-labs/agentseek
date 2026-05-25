"""``agentseek skills`` — thin wrapper around ``npx-skills`` via ``uvx``.

`npx-skills <https://pypi.org/project/npx-skills/>`_ is a ``uv``-installable
Python wrapper around the upstream ``vercel-labs/skills`` CLI (ships its own
Node runtime). We expose its subcommands verbatim — ``add``, ``list``,
``find``, ``update``, ``remove``, ``init`` — and forward every flag through,
including those we don't know about. This keeps AgentSeek aligned with
whatever the upstream CLI adds without us re-issuing patches.

Install paths follow upstream conventions: project-scope skills land in
``./<agent>/skills/`` (e.g. ``./.claude/skills/``), global skills in
``~/<agent>/skills/``. AgentSeek does **not** rewrite those paths — pass
``--dir <path>`` to run the whole invocation from a different workspace.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from agentseek_cli._proc import run_uvx

NPX_SKILLS_DIST = "npx-skills"
SKILLS_COMMANDS: tuple[str, ...] = ("add", "list", "find", "update", "remove", "init")

_PASSTHROUGH_CONTEXT_SETTINGS = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "help_option_names": [],
}

app = typer.Typer(
    name="skills",
    help=("Manage agent skills via the upstream `vercel-labs/skills` CLI (invoked through `uvx npx-skills`)."),
    add_completion=False,
    no_args_is_help=True,
)


@app.callback()
def _skills_root(
    ctx: typer.Context,
    workspace: Annotated[
        Path | None,
        typer.Option(
            "--dir",
            help="Workspace directory to run `skills` in. Defaults to the current working directory.",
            show_default=False,
        ),
    ] = None,
) -> None:
    resolved = (workspace or Path.cwd()).resolve()
    ctx.ensure_object(dict)["cwd"] = resolved


def _forward(ctx: typer.Context, command: str) -> None:
    cwd = ctx.ensure_object(dict).get("cwd", Path.cwd())
    exit_code = run_uvx(NPX_SKILLS_DIST, [command, *list(ctx.args)], cwd=cwd)
    raise typer.Exit(exit_code)


def _passthrough(command: str):
    def _command(ctx: typer.Context) -> None:
        _forward(ctx, command)

    _command.__name__ = f"skills_{command}"
    _command.__doc__ = f"Forward `{command}` to `npx-skills`."
    return _command


for _command_name in SKILLS_COMMANDS:
    app.command(_command_name, context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)(_passthrough(_command_name))


__all__ = ["NPX_SKILLS_DIST", "SKILLS_COMMANDS", "app"]
