"""``agentseek skills`` — thin wrapper around the ``npx-skills`` CLI.

`npx-skills <https://pypi.org/project/npx-skills/>`_ is bundled as a direct
dependency of ``agentseek-cli``. We expose its subcommands verbatim — ``add``,
``list``, ``find``, ``update``, ``remove``, ``init`` — and forward every flag
through, including those we don't know about. This keeps AgentSeek aligned
with whatever the upstream CLI adds without us re-issuing patches.

**Default source for ``add``:** When no positional source argument is given,
``ob-labs/agentseek`` is used automatically. This lets developers run
``agentseek skills add --all --global`` without remembering the repo path.

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

DEFAULT_SOURCE = "ob-labs/agentseek"

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


def _find_skills_cmd() -> list[str]:
    """Return the command prefix for invoking the skills CLI.

    Checks in order:
    1. ``npx-skills`` (Python package, bundled dependency)
    2. ``npx skills`` (Node.js npx, widely available)

    Returns the base command as a list (e.g. ["/usr/bin/npx-skills"] or ["npx", "skills"]).
    """
    path = shutil.which("npx-skills")
    if path is not None:
        return [path]
    npx = shutil.which("npx")
    if npx is not None:
        return [npx, "skills"]
    typer.echo(
        "Neither `npx-skills` nor `npx` was found on PATH.\n"
        "Install one of:\n"
        "  • `uv pip install npx-skills` (Python package)\n"
        "  • Node.js (provides npx): https://nodejs.org/",
        err=True,
    )
    raise typer.Exit(1)


def _forward(ctx: typer.Context, command: str) -> None:
    cwd = ctx.ensure_object(dict).get("cwd", Path.cwd())
    base = _find_skills_cmd()
    cmd = [*base, command, *list(ctx.args)]
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)  # noqa: S603
    raise typer.Exit(completed.returncode)


# Flags that consume the next token as a value (not a positional source).
# Maintenance: if upstream `npx-skills add` introduces new flags with required
# values, add them here — otherwise the value may be mistaken for a source arg.
_FLAGS_WITH_VALUE = frozenset({
    "-s",
    "--skill",
    "-a",
    "--agent",
    "-o",
    "--output",
    "--dir",
})


def _has_positional_source(args: list[str]) -> bool:
    """Check if args contain a positional source argument (not a flag value)."""
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
            continue
        if arg in _FLAGS_WITH_VALUE:
            skip_next = True
            continue
        if arg.startswith("-"):
            continue
        return True
    return False


@app.command("add", context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)
def skills_add(ctx: typer.Context) -> None:
    """Install skills. Defaults to ob-labs/agentseek when no source is given."""
    cwd = ctx.ensure_object(dict).get("cwd", Path.cwd())
    base = _find_skills_cmd()
    args = list(ctx.args)
    if not _has_positional_source(args):
        args.insert(0, DEFAULT_SOURCE)
    cmd = [*base, "add", *args]
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)  # noqa: S603
    raise typer.Exit(completed.returncode)


def _passthrough(command: str):
    def _command(ctx: typer.Context) -> None:
        _forward(ctx, command)

    _command.__name__ = f"skills_{command}"
    _command.__doc__ = f"Forward `{command}` to `npx-skills`."
    return _command


for _command_name in SKILLS_COMMANDS:
    if _command_name == "add":
        continue
    app.command(_command_name, context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)(_passthrough(_command_name))


__all__ = ["SKILLS_COMMANDS", "app"]
