"""``agentseek skills`` — thin wrapper around the ``npx-skills`` CLI.

`npx-skills <https://pypi.org/project/npx-skills/>`_ is bundled as a direct
dependency of ``agentseek-cli``. We expose its subcommands verbatim — ``add``,
``list``, ``find``, ``update``, ``remove``, ``init`` — and forward every flag
through, including those we don't know about. This keeps AgentSeek aligned
with whatever the upstream CLI adds without us re-issuing patches.

**Default source for ``add``:** When the first ``add`` argument is not an
explicit source, ``ob-labs/agentseek`` is inserted before the user-provided
arguments. A bare ``agentseek skills add`` selects all AgentSeek skills while
leaving scope and confirmation to upstream.

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

# Embedded catalogue avoids cloning the full repo just to list AgentSeek skills.
# Update this when adding/removing skills in the skills/ directory.
SKILLS_CATALOGUE: tuple[tuple[str, str], ...] = (
    ("langsmith-trace", "LangSmith CLI setup, tracing, and trace debugging for AgentSeek backends"),
    ("langchain-dev-guide", "LangChain / LangGraph engineering pitfalls and verified fixes"),
    ("langchain-cn-models", "Integrate Chinese LLM providers (DeepSeek, Qwen, GLM) into LangChain"),
    ("github-repo-cards", "Generate visual GitHub repo cards for documentation and social sharing"),
)

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


def _has_leading_source(args: list[str]) -> bool:
    return bool(args) and not args[0].startswith("-")


@app.command("add", context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)
def skills_add(ctx: typer.Context) -> None:
    """Install AgentSeek skills by default, or use an explicit source."""
    cwd = ctx.ensure_object(dict).get("cwd", Path.cwd())
    base = _find_skills_cmd()
    args = list(ctx.args)
    if _has_leading_source(args):
        cmd = [*base, "add", *args]
    elif args:
        cmd = [*base, "add", DEFAULT_SOURCE, *args]
    else:
        cmd = [*base, "add", DEFAULT_SOURCE, "--all"]
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)  # noqa: S603
    raise typer.Exit(completed.returncode)


@app.command("list", context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)
def skills_list(ctx: typer.Context) -> None:
    """List the embedded AgentSeek catalogue, or pass args through."""
    args = list(ctx.args)
    if args:
        cwd = ctx.ensure_object(dict).get("cwd", Path.cwd())
        base = _find_skills_cmd()
        cmd = [*base, "list", *args]
        completed = subprocess.run(cmd, cwd=str(cwd), check=False)  # noqa: S603
        raise typer.Exit(completed.returncode)

    typer.echo(f"\n  AgentSeek Skills ({DEFAULT_SOURCE})\n")
    for name, description in SKILLS_CATALOGUE:
        typer.echo(f"    {name}")
        typer.echo(f"      {description}\n")
    typer.echo("  Install:")
    typer.echo("    agentseek skills add --all --global        # all skills")
    typer.echo("    agentseek skills add --skill <name> -g     # one skill\n")


def _passthrough(command: str):
    def _command(ctx: typer.Context) -> None:
        _forward(ctx, command)

    _command.__name__ = f"skills_{command}"
    _command.__doc__ = f"Forward `{command}` to `npx-skills`."
    return _command


for _command_name in SKILLS_COMMANDS:
    if _command_name in {"add", "list"}:
        continue
    app.command(_command_name, context_settings=_PASSTHROUGH_CONTEXT_SETTINGS)(_passthrough(_command_name))


__all__ = ["SKILLS_COMMANDS", "app"]
