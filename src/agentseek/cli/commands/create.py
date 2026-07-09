"""``agentseek create`` — scaffold a new agent project from a cookiecutter template.

Templates live in the ``templates/`` directory at the **repository root** (next
to ``contrib/``).  At runtime the command resolves them in two ways:

1. **Local checkout** — when running from the cloned repo (detected via
   ``git rev-parse --show-toplevel``), templates are read straight from disk.
   This gives instant feedback during development: edit a template, run
   ``agentseek create``, see the result.

2. **Installed / remote** — when the package is ``pip install``-ed without
   a working tree, the command prepares the repository in cookiecutter's cache
   first, then reads templates from that cached checkout.

Spec resolution:

* ``agentseek create``                                — interactive type + template selection.
* ``agentseek create bub``                            — ``templates/bub/default``.
* ``agentseek create bub/default``                    — ``templates/bub/default``.
* ``agentseek create bub --list-templates``           — list templates available for the type.
* ``agentseek create --list-templates --filter rag``  — list templates matching a keyword.
* ``agentseek create bub --template default``         — same as ``bub/default``.
* ``agentseek create bub --template``                 — list templates for the type (same as --list-templates).
* ``agentseek create --template``                     — list all templates across all types.
* ``agentseek create deepagents --output-dir /tmp``   — write the generated project under /tmp.
* ``agentseek create https://github.com/x/y.git``    — passthrough to cookiecutter.
* ``agentseek create /path/to/template``              — passthrough to cookiecutter.
"""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import typer
from typer.core import TyperGroup

# ---------------------------------------------------------------------------
# Typer plumbing
# ---------------------------------------------------------------------------


class _SwallowArgsGroup(TyperGroup):
    """Typer group that forwards every trailing token to the callback.

    Typer normally treats the first positional after the group name as a
    sub-command, so ``agentseek create deepagents --template default`` is
    rejected with "No such command 'deepagents'". We override
    ``parse_args`` to dump everything past the group's own options into
    ``ctx.args``, leaving callback-side argparse to interpret them.
    """

    def parse_args(self, ctx: Any, args: list[str]) -> list[str]:
        ctx.args = list(args)
        return []


app = typer.Typer(
    name="create",
    help="Scaffold a new agent project from a pre-built template.",
    add_completion=False,
    no_args_is_help=False,
    cls=_SwallowArgsGroup,
)

KNOWN_TYPES: tuple[str, ...] = ("bub", "deepagents", "langchain")
DEFAULT_TYPE = "bub"

_TEMPLATE_LIST_SENTINEL = "__list__"

# The canonical GitHub repo URL used when templates are not found locally.
REPO_URL = "https://github.com/ob-labs/agentseek"
REPO_GIT_URL = f"{REPO_URL}.git"
# The directory inside the repo that holds all cookiecutter templates.
TEMPLATES_DIR = "templates"
TEMPLATE_REPO_CACHE_DIR = "agentseek"


# ---------------------------------------------------------------------------
# Template source resolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TemplateSource:
    """Resolved template location ready for ``cookiecutter()``."""

    template: str  # local path or remote URL
    directory: str | None = None  # cookiecutter ``directory`` kwarg (monorepo subdir)
    checkout: str | None = None  # cookiecutter ``checkout`` kwarg (branch / tag)
    install_source_path: str | None = None  # local monorepo path for generated project deps
    install_source_url: str | None = None  # remote repo URL for generated project deps


def _git_toplevel() -> Path | None:
    """Return the repository root if we are inside a git working tree."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def _local_templates_root() -> Path | None:
    """Return ``<repo-root>/templates`` if it exists on disk.

    Resolution strategy (in order):

    1. Walk up from *this* source file looking for a ``templates/`` directory
       that contains at least one ``cookiecutter.json``.  This works regardless
       of the user's cwd, which is important because the user will typically
       ``cd`` into their desired output directory before running ``create``.
    2. Fall back to ``git rev-parse --show-toplevel`` (covers unusual layouts).
    """
    # Strategy 1: relative to source file.
    anchor: Path | None = Path(__file__).resolve().parent
    while anchor and anchor != anchor.parent:
        candidate = anchor / TEMPLATES_DIR
        if candidate.is_dir() and any(candidate.rglob("cookiecutter.json")):
            return candidate
        anchor = anchor.parent

    # Strategy 2: git toplevel.
    repo = _git_toplevel()
    if repo is not None:
        candidate = repo / TEMPLATES_DIR
        if candidate.is_dir():
            return candidate

    return None


def _resolve_type_template(
    project_type: str,
    template_name: str,
    *,
    templates_root: Path,
) -> TemplateSource:
    """Resolve ``<type>/<name>`` from an already prepared template root."""
    template_path = templates_root / project_type / template_name
    if (template_path / "cookiecutter.json").is_file():
        install_source_path = str(templates_root.parent) if _local_templates_root() == templates_root else None
        return TemplateSource(
            template=str(template_path),
            install_source_path=install_source_path,
            install_source_url=None if install_source_path else REPO_GIT_URL,
        )
    _print_unknown_template(project_type, template_name, templates_root=templates_root)
    raise typer.Exit(2)


def _is_external_spec(spec: str) -> bool:
    """Return ``True`` if *spec* looks like a URL or absolute local path."""
    return spec.startswith(("https://", "http://", "git@", "gh:", "/"))


# ---------------------------------------------------------------------------
# Template listing / discovery
# ---------------------------------------------------------------------------


def _list_templates(project_type: str, templates_root: Path | None = None) -> list[str]:
    """Return template names available under ``templates/<type>/``."""
    if templates_root is None:
        templates_root = _local_templates_root()
    if templates_root is None:
        return []
    type_dir = templates_root / project_type
    if not type_dir.is_dir():
        return []
    return sorted(entry.name for entry in type_dir.iterdir() if (entry / "cookiecutter.json").is_file())


def _prepare_templates_root(checkout: str | None = None) -> Path:
    local_root = _local_templates_root()
    if local_root is not None:
        return local_root

    from cookiecutter.config import get_user_config
    from cookiecutter.vcs import clone

    cookiecutters_dir = Path(get_user_config()["cookiecutters_dir"]).expanduser()
    cached_repo = cookiecutters_dir / TEMPLATE_REPO_CACHE_DIR
    if checkout is None and cached_repo.is_dir():
        templates_root = cached_repo / TEMPLATES_DIR
    else:
        repo_root = clone(
            REPO_URL,
            checkout=checkout,
            clone_to_dir=cookiecutters_dir,
            no_input=True,
        )
        templates_root = Path(repo_root) / TEMPLATES_DIR

    if not templates_root.is_dir():
        typer.echo(f"Templates directory not found at {templates_root}.", err=True)
        raise typer.Exit(1)
    return templates_root


def _load_template_descriptions(templates_root: Path | None = None) -> dict[str, str]:
    if templates_root is None:
        templates_root = _local_templates_root()
    if templates_root is None:
        return {}
    index = templates_root / "index.json"
    if not index.is_file():
        return {}
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def _print_templates_table(
    project_type: str,
    templates: list[str],
    descriptions: dict[str, str] | None = None,
    *,
    filter_keyword: str | None = None,
) -> None:
    if not templates:
        if filter_keyword:
            typer.echo(f"No templates matched filter {filter_keyword!r} for type {project_type!r}.")
            return
        typer.echo(f"No templates found for type {project_type!r}.")
        return
    if descriptions is None:
        descriptions = _load_template_descriptions()
    typer.echo(f"\n  {project_type} ({len(templates)} templates)")
    typer.echo(f"  {'─' * 60}")
    for name in templates:
        key = f"{project_type}/{name}"
        desc = descriptions.get(key, "")
        typer.echo(f"    {key}")
        if desc:
            typer.echo(f"      {desc}")


def _template_matches_filter(project_type: str, template_name: str, descriptions: dict[str, str], keyword: str) -> bool:
    key = f"{project_type}/{template_name}"
    haystack = f"{key}\n{descriptions.get(key, '')}".casefold()
    return keyword.casefold() in haystack


def _filter_templates(
    project_type: str,
    templates: list[str],
    descriptions: dict[str, str],
    filter_keyword: str | None,
) -> list[str]:
    if not filter_keyword:
        return templates
    return [name for name in templates if _template_matches_filter(project_type, name, descriptions, filter_keyword)]


def _print_all_templates(
    templates_root: Path,
    descriptions: dict[str, str],
    *,
    filter_keyword: str | None = None,
) -> None:
    """Print all templates across all types with usage hints."""
    total = 0
    for project_type in KNOWN_TYPES:
        templates = _filter_templates(
            project_type, _list_templates(project_type, templates_root), descriptions, filter_keyword
        )
        total += len(templates)
        if templates or filter_keyword is None:
            _print_templates_table(project_type, templates, descriptions)
    if filter_keyword and not total:
        typer.echo(f"No templates matched filter {filter_keyword!r}.")
        return
    if total:
        typer.echo("\n  Usage:")
        if filter_keyword:
            typer.echo("    agentseek create <type>/<name>")
        else:
            typer.echo("    agentseek create <type>/<name>       e.g. agentseek create bub/default")
        typer.echo("    agentseek create <type>              use default template for the type")
        typer.echo("    agentseek create                     interactive selection")
        typer.echo()


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------


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


def _prompt_template_name(
    project_type: str,
    templates: list[str],
    descriptions: dict[str, str] | None = None,
) -> str:
    if len(templates) == 1:
        return templates[0]
    if descriptions is None:
        descriptions = _load_template_descriptions()
    typer.echo(f"Available {project_type} templates:")
    width = max(len(name) for name in templates)
    for index, name in enumerate(templates, start=1):
        desc = descriptions.get(f"{project_type}/{name}", "")
        suffix = f"  — {desc}" if desc else ""
        typer.echo(f"  {index}. {name:<{width}}{suffix}")
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


# ---------------------------------------------------------------------------
# Cookiecutter invocation
# ---------------------------------------------------------------------------


def _run_cookiecutter(
    source: TemplateSource,
    *,
    output_dir: Path,
    no_input: bool,
) -> Path | None:
    """Invoke cookiecutter; isolated so tests can monkeypatch."""
    from cookiecutter.exceptions import OutputDirExistsException
    from cookiecutter.main import cookiecutter

    try:
        generated = cookiecutter(
            template=source.template,
            output_dir=str(output_dir),
            no_input=no_input,
            directory=source.directory,
            checkout=source.checkout,
            extra_context={
                "_agentseek_source_path": source.install_source_path or "",
                "_agentseek_source_url": source.install_source_url or REPO_GIT_URL,
            },
        )
        return Path(generated) if generated else None
    except OutputDirExistsException:
        typer.echo(
            "Target directory already exists. Remove it first or choose a different location.",
            err=True,
        )
        raise typer.Exit(1) from None


# ---------------------------------------------------------------------------
# Argparse CLI surface
# ---------------------------------------------------------------------------


def _parse_argv(argv: list[str]) -> argparse.Namespace:
    """Parse the raw create argv with argparse.

    Using argparse here (instead of additional Typer ``Option``s) keeps the
    documented ``agentseek create [SPEC] [--option ...]`` shape intact even
    though Typer would otherwise insist on a ``COMMAND`` after the positional.
    """
    parser = argparse.ArgumentParser(
        prog="agentseek create",
        add_help=True,
        description="Scaffold a new agent project from a pre-built template.",
    )
    parser.add_argument(
        "spec",
        nargs="?",
        default=None,
        help=(
            "Template spec. Can be a framework type (bub, deepagents, langchain), "
            "a type/name pair (bub/default), a git URL, or a local path."
        ),
    )
    parser.add_argument(
        "--template",
        nargs="?",
        default=None,
        const=_TEMPLATE_LIST_SENTINEL,
        help=(
            "Named template under the chosen type (e.g. --template default). "
            "Pass --template with no value to list available templates."
        ),
    )
    parser.add_argument(
        "--checkout",
        default=None,
        help="Branch, tag, or commit to checkout when fetching from a remote repository.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory where the generated project should be written.",
    )
    parser.add_argument(
        "--list-templates",
        action="store_true",
        help="List templates available for the chosen type and exit.",
    )
    parser.add_argument(
        "--filter",
        default=None,
        help="Keyword used to filter listed templates by spec or description.",
    )
    parser.add_argument(
        "--no-input",
        action="store_true",
        help="Skip cookiecutter prompts (use template defaults).",
    )
    parser.add_argument(
        "--describe",
        action="store_true",
        help=(
            "Print template description and configuration without generating a project. "
            "Use with a spec like ``agentseek create bub/default --describe``."
        ),
    )
    return parser.parse_args(argv)


def _load_cookiecutter_context(template_dir: Path) -> dict[str, object] | None:
    """Load ``cookiecutter.json`` from *template_dir* if it exists."""
    cookiecutter_json = template_dir / "cookiecutter.json"
    if not cookiecutter_json.is_file():
        return None
    try:
        data = json.loads(cookiecutter_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def _describe_template(
    source: TemplateSource,
    *,
    templates_root: Path,
) -> None:
    """Print template spec, description, and cookiecutter variables.

    Does **not** run cookiecutter or create any files.
    """
    template_dir = Path(source.template)

    # Build a clean key (e.g. "bub/default") from the templates root.
    try:
        rel = template_dir.relative_to(templates_root)
        parts = rel.parts
        spec_key = f"{parts[0]}/{parts[1]}" if len(parts) >= 2 else str(rel)
    except ValueError:
        spec_key = f"{template_dir.parent.name}/{template_dir.name}"

    descriptions = _load_template_descriptions(templates_root)
    description = descriptions.get(spec_key, "")

    typer.echo(f"\n  Template: {spec_key}")
    typer.echo(f"  {'─' * 60}")
    if description:
        typer.echo(f"  Description: {description}")
    else:
        typer.echo("  Description: (none)")

    typer.echo(f"  Path: {template_dir}")

    context = _load_cookiecutter_context(template_dir)
    if context is None:
        typer.echo("  Cookiecutter variables: (none)")
        typer.echo()
        return

    typer.echo(f"  Cookiecutter variables ({len(context)}):")
    for key, value in context.items():
        display = value if isinstance(value, str) else json.dumps(value)
        # Truncate long values for readability.
        if len(display) > 80:
            display = display[:77] + "..."
        typer.echo(f"    {key}: {display}")
    typer.echo()


def _handle_external_spec(args: argparse.Namespace) -> None:
    """Run cookiecutter for external specs unless describe mode is requested."""
    if args.describe:
        typer.echo(
            "--describe only supports bundled templates such as 'bub/default'.",
            err=True,
        )
        raise typer.Exit(2)

    source = TemplateSource(
        template=args.spec,
        directory=args.template,  # --template doubles as directory for external
        checkout=args.checkout,
    )
    output_dir = args.output_dir if args.output_dir is not None else Path.cwd()
    generated = _run_cookiecutter(source, output_dir=output_dir, no_input=args.no_input)
    _print_created_next_steps(generated, base_dir=Path.cwd())


# ---------------------------------------------------------------------------
# Main callback
# ---------------------------------------------------------------------------


@app.callback(invoke_without_command=True)
def create(ctx: typer.Context) -> None:
    """Scaffold a new agent project from a pre-built template."""
    args = _parse_new_args(ctx)
    output_dir = args.output_dir if args.output_dir is not None else Path.cwd()

    # --- External spec (URL or absolute path) → passthrough to cookiecutter ---
    if args.spec and _is_external_spec(args.spec):
        _handle_external_spec(args)
        return

    # --- Parse spec into (type, name) ---
    project_type, template_name = _split_spec(args)

    # --- --list-templates or --template (no value) ---
    if args.list_templates or args.template == _TEMPLATE_LIST_SENTINEL:
        _show_templates(project_type, checkout=args.checkout, filter_keyword=args.filter)
        return

    templates_root = _prepare_templates_root(checkout=args.checkout)

    # --- Interactive type selection if needed ---
    if project_type is None:
        project_type = _prompt_project_type()

    _validate_project_type(project_type)

    # --- Resolve template name ---
    if template_name is None:
        template_name = args.template
    if template_name is None:
        if args.no_input:
            template_name = "default"
        else:
            descriptions = _load_template_descriptions(templates_root)
            available = _list_templates(project_type, templates_root)
            if not available:
                template_name = "default"
            elif len(available) == 1:
                template_name = available[0]
            else:
                template_name = _prompt_template_name(project_type, available, descriptions)

    source = _resolve_type_template(
        project_type,
        template_name,
        templates_root=templates_root,
    )

    # --- --describe: print template info without generating ---
    if args.describe:
        _describe_template(source, templates_root=templates_root)
        return

    generated = _run_cookiecutter(source, output_dir=output_dir, no_input=args.no_input)
    _print_created_next_steps(generated, base_dir=Path.cwd())


def _parse_new_args(ctx: typer.Context) -> argparse.Namespace:
    try:
        return _parse_argv(list(ctx.args))
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 2
        raise typer.Exit(code) from exc


def _split_spec(args: argparse.Namespace) -> tuple[str | None, str | None]:
    """Split the positional spec into ``(type, name)``.

    Returns ``(None, None)`` when no spec was given (interactive mode).
    """
    spec = args.spec
    if spec is None:
        return None, None
    # "bub/default" → ("bub", "default")
    if "/" in spec and not _is_external_spec(spec):
        parts = spec.split("/", 1)
        return parts[0], parts[1]
    # "bub" → ("bub", None) — name resolved later
    return spec, None


def _validate_project_type(project_type: str) -> None:
    if project_type not in KNOWN_TYPES:
        typer.echo(
            f"Unknown framework type {project_type!r}. Expected one of: {', '.join(KNOWN_TYPES)}.",
            err=True,
        )
        raise typer.Exit(2)


def _print_unknown_template(project_type: str, template_name: str, *, templates_root: Path) -> None:
    available = _list_templates(project_type, templates_root)
    typer.echo(f"Template {project_type}/{template_name} was not found. Supported templates:", err=True)
    _print_templates_table(project_type, available, _load_template_descriptions(templates_root))


def _show_templates(
    project_type: str | None,
    *,
    checkout: str | None = None,
    filter_keyword: str | None = None,
) -> None:
    if project_type is not None:
        _validate_project_type(project_type)
    templates_root = _prepare_templates_root(checkout=checkout)
    descriptions = _load_template_descriptions(templates_root)
    if project_type is None:
        _print_all_templates(templates_root, descriptions, filter_keyword=filter_keyword)
        return
    templates = _filter_templates(
        project_type, _list_templates(project_type, templates_root), descriptions, filter_keyword
    )
    _print_templates_table(project_type, templates, descriptions, filter_keyword=filter_keyword)
    typer.echo()


def _print_created_next_steps(generated: Path | None, *, base_dir: Path) -> None:
    if generated is None:
        return
    display_path = _display_generated_path(generated, base_dir=base_dir)
    typer.echo(f"Created {display_path}")
    typer.echo()
    typer.echo("Next:")
    typer.echo(f"  cd {shlex.quote(display_path)}")
    typer.echo("  agentseek info")
    typer.echo("  agentseek task --list")
    typer.echo("  agentseek doctor")


def _display_generated_path(generated: Path, *, base_dir: Path) -> str:
    try:
        return str(generated.resolve().relative_to(base_dir.resolve()))
    except ValueError:
        return str(generated)


__all__ = ["DEFAULT_TYPE", "KNOWN_TYPES", "REPO_URL", "TemplateSource", "app"]
