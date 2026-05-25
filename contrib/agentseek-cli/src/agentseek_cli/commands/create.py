"""``agentseek create`` — scaffold a new agent project from a cookiecutter template.

Templates ship inside ``agentseek_cli.templates``; we list them by scanning the
on-disk subtree and resolve them by ``<type>/<name>`` keys.

CLI shape (matches the documented surface):

* ``agentseek create``                          — interactive type + template selection.
* ``agentseek create deepagents``               — use the default template for the type.
* ``agentseek create langchain --list-templates`` — list templates available for the type.
* ``agentseek create bub --template chat``      — use a specific template.

The ``--template`` flag with no value form documented in older drafts is
expressed here as ``--list-templates`` because Typer / Click cannot bind a
flag-like option whose value is optional without ambiguity.

We parse args manually inside the typer callback (``ignore_unknown_options``
+ ``allow_extra_args``) because Typer treats a positional ``Argument`` plus
trailing ``Option`` flags as a click group + sub-commands, which trips on
``agentseek create deepagents --template default``.
"""

from __future__ import annotations

import argparse
import json
from importlib.resources import as_file, files
from pathlib import Path

import click
import typer
from typer.core import TyperGroup


class _SwallowArgsGroup(TyperGroup):
    """Typer group that forwards every trailing token to the callback.

    Typer normally treats the first positional after the group name as a
    sub-command, so ``agentseek create deepagents --template default`` is
    rejected with "No such command 'deepagents'". We override
    ``parse_args`` to dump everything past the group's own options into
    ``ctx.args``, leaving callback-side argparse to interpret them.
    """

    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        ctx.args = list(args)
        return []


app = typer.Typer(
    name="create",
    help="Create a new agent project from a pre-built template.",
    add_completion=False,
    no_args_is_help=False,
    cls=_SwallowArgsGroup,
)

KNOWN_TYPES: tuple[str, ...] = ("deepagents", "langchain", "bub")
DEFAULT_TYPE = "deepagents"


def _templates_root() -> Path:
    """Return the on-disk directory holding bundled templates.

    The ``files()`` API works for both wheel installs and editable layouts; we
    materialize to a real path because cookiecutter shells out and needs one.
    """
    resource = files("agentseek_cli").joinpath("templates")
    with as_file(resource) as path:
        return Path(path)


def _list_templates(project_type: str) -> list[str]:
    """Return template names available under ``templates/<type>/``."""
    type_dir = _templates_root() / project_type
    if not type_dir.is_dir():
        return []
    names = [entry.name for entry in type_dir.iterdir() if (entry / "cookiecutter.json").is_file()]
    return sorted(names)


def _resolve_template(project_type: str, name: str) -> Path:
    """Return the absolute path of ``templates/<type>/<name>``.

    Raises ``FileNotFoundError`` with a user-friendly message if missing.
    """
    candidate = _templates_root() / project_type / name
    if not (candidate / "cookiecutter.json").is_file():
        available = _list_templates(project_type)
        hint = ", ".join(available) if available else "<none bundled>"
        msg = f"Template {name!r} not found under {project_type!r}. Available: {hint}."
        raise FileNotFoundError(msg)
    return candidate


def _load_template_descriptions() -> dict[str, str]:
    """Best-effort load of the bundled templates ``index.json`` for descriptions."""
    index = _templates_root() / "index.json"
    if not index.is_file():
        return {}
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def _print_templates_table(project_type: str, templates: list[str]) -> None:
    if not templates:
        typer.echo(f"No templates bundled for type {project_type!r}.")
        return
    descriptions = _load_template_descriptions()
    typer.echo(f"Available {project_type} templates:")
    width = max(len(name) for name in templates)
    for name in templates:
        key = f"{project_type}/{name}"
        desc = descriptions.get(key, "")
        suffix = f"  {desc}" if desc else ""
        typer.echo(f"  {name:<{width}}{suffix}")


def _prompt_project_type() -> str:
    typer.echo("Select an agent framework type:")
    for index, name in enumerate(KNOWN_TYPES, start=1):
        marker = " (default)" if name == DEFAULT_TYPE else ""
        typer.echo(f"  {index}. {name}{marker}")
    raw = typer.prompt(
        f"Choose [1-{len(KNOWN_TYPES)}]",
        default=str(KNOWN_TYPES.index(DEFAULT_TYPE) + 1),
    )
    return _coerce_type_choice(raw)


def _coerce_type_choice(raw: str) -> str:
    cleaned = raw.strip().lower()
    if cleaned in KNOWN_TYPES:
        return cleaned
    if cleaned.isdigit():
        index = int(cleaned) - 1
        if 0 <= index < len(KNOWN_TYPES):
            return KNOWN_TYPES[index]
    msg = f"Invalid choice {raw!r}. Expected a number 1-{len(KNOWN_TYPES)} or one of: {', '.join(KNOWN_TYPES)}."
    raise typer.BadParameter(msg)


def _prompt_template_name(project_type: str, templates: list[str]) -> str:
    if len(templates) == 1:
        return templates[0]
    typer.echo(f"Available {project_type} templates:")
    for index, name in enumerate(templates, start=1):
        typer.echo(f"  {index}. {name}")
    raw = typer.prompt(f"Choose template [1-{len(templates)}]", default="1")
    cleaned = raw.strip()
    if cleaned in templates:
        return cleaned
    if cleaned.isdigit():
        index = int(cleaned) - 1
        if 0 <= index < len(templates):
            return templates[index]
    msg = f"Invalid choice {raw!r}."
    raise typer.BadParameter(msg)


def _run_cookiecutter(template_path: Path, *, output_dir: Path, no_input: bool) -> None:
    """Invoke cookiecutter; isolated so tests can monkeypatch."""
    from cookiecutter.main import cookiecutter

    cookiecutter(str(template_path), output_dir=str(output_dir), no_input=no_input)


def _parse_argv(argv: list[str]) -> argparse.Namespace:
    """Parse the raw create argv with argparse.

    Using argparse here (instead of additional Typer ``Option``s) keeps the
    documented ``agentseek create [TYPE] [--option ...]`` shape intact even
    though Typer would otherwise insist on a ``COMMAND`` after the positional.
    """
    parser = argparse.ArgumentParser(
        prog="agentseek create",
        add_help=False,
        description="Create a new agent project from a pre-built template.",
    )
    parser.add_argument(
        "type",
        nargs="?",
        choices=KNOWN_TYPES,
        default=None,
        help=f"Agent framework type. One of: {', '.join(KNOWN_TYPES)}.",
    )
    parser.add_argument("--template", default=None, help="Pull a named template under the chosen type.")
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List templates available for the chosen type and exit.",
    )
    parser.add_argument(
        "--no-input",
        action="store_true",
        help="Skip cookiecutter prompts (use template defaults).",
    )
    return parser.parse_args(argv)


@app.callback(invoke_without_command=True)
def create(ctx: typer.Context) -> None:
    """Create a new agent project from a pre-built template."""

    args = _parse_create_args(ctx)
    project_type = _resolve_project_type(args)

    if args.list_templates:
        _show_templates(project_type)
        return

    if project_type is None:
        # Defensive: _resolve_project_type returned None only when list_templates is True.
        raise typer.Exit(2)

    available = _list_templates(project_type)
    if not available:
        typer.echo(f"No templates bundled for type {project_type!r}.", err=True)
        raise typer.Exit(2)

    template = _resolve_template_name(args, project_type, available)
    template_path = _safely_resolve_template(project_type, template)
    _run_cookiecutter(template_path, output_dir=Path.cwd(), no_input=args.no_input)


def _parse_create_args(ctx: typer.Context) -> argparse.Namespace:
    try:
        return _parse_argv(list(ctx.args))
    except SystemExit as exc:
        # argparse already wrote its error to stderr; preserve its exit code.
        raise typer.Exit(int(exc.code or 2)) from exc


def _resolve_project_type(args: argparse.Namespace) -> str | None:
    project_type = args.type
    if project_type is None and not args.list_templates:
        project_type = _prompt_project_type()
    if project_type is not None and project_type not in KNOWN_TYPES:
        typer.echo(
            f"Unknown framework type {project_type!r}. Expected one of: {', '.join(KNOWN_TYPES)}.",
            err=True,
        )
        raise typer.Exit(2)
    return project_type


def _show_templates(project_type: str | None) -> None:
    if project_type is None:
        for known in KNOWN_TYPES:
            _print_templates_table(known, _list_templates(known))
        return
    _print_templates_table(project_type, _list_templates(project_type))


def _resolve_template_name(args: argparse.Namespace, project_type: str, available: list[str]) -> str:
    template = args.template
    if template:
        return template
    if len(available) == 1 or args.no_input:
        return available[0] if "default" not in available else "default"
    return _prompt_template_name(project_type, available)


def _safely_resolve_template(project_type: str, template: str) -> Path:
    try:
        return _resolve_template(project_type, template)
    except FileNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(2) from exc


__all__ = ["DEFAULT_TYPE", "KNOWN_TYPES", "app"]
