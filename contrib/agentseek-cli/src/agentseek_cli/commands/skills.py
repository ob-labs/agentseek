"""``agentseek skills`` — thin wrapper around the ``npx-skills`` CLI.

`npx-skills <https://pypi.org/project/npx-skills/>`_ is bundled as a direct
dependency of ``agentseek-cli``. We expose its subcommands verbatim — ``add``,
``list``, ``find``, ``update``, ``remove``, ``init`` — and forward every flag
through, including those we don't know about. This keeps AgentSeek aligned
with whatever the upstream CLI adds without us re-issuing patches.

Install paths follow upstream conventions: project-scope skills land in
``./<agent>/skills/`` (e.g. ``./.claude/skills/``), global skills in
``~/<agent>/skills/``. AgentSeek does **not** rewrite those paths — pass
``--dir <path>`` to run the whole invocation from a different workspace.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer

SKILLS_COMMANDS: tuple[str, ...] = ("add", "list", "find", "update", "remove", "init")

_PASSTHROUGH_CONTEXT_SETTINGS = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "help_option_names": [],
}

app = typer.Typer(
    name="skills",
    help="Manage agent skills via the upstream `vercel-labs/skills` CLI.",
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


def _find_npx_skills() -> str:
    """Return the resolved ``npx-skills`` executable path or raise a friendly error."""
    path = shutil.which("npx-skills")
    if path is None:
        typer.echo(
            "`npx-skills` was not found on PATH. "
            "It should be installed as a dependency of agentseek-cli.\n"
            "Try: `uv pip install npx-skills` or reinstall agentseek-cli.",
            err=True,
        )
        raise typer.Exit(1)
    return path


def _forward(ctx: typer.Context, command: str) -> None:
    cwd = ctx.ensure_object(dict).get("cwd", Path.cwd())
    npx_skills = _find_npx_skills()
    cmd = [npx_skills, command, *list(ctx.args)]
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)  # noqa: S603
    raise typer.Exit(completed.returncode)


def _passthrough(command: str):
    def _command(ctx: typer.Context) -> None:
        _forward(ctx, command)

    _command.__name__ = f"skills_{command}"
    _command.__doc__ = f"Forward `{command}` to `npx-skills`."
    return _command


for _command_name in SKILLS_COMMANDS:
    app.command(_command_name, context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)(_passthrough(_command_name))


__all__ = ["SKILLS_COMMANDS", "app"]
