"""``agentseek plugin`` — inspect, install, uninstall, and update runtime plugins."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import typer

from agentseek.env import DEFAULT_PLUGIN_SANDBOX

app = typer.Typer(
    name="plugin",
    help="Manage AgentSeek runtime plugins.",
    add_completion=False,
    no_args_is_help=True,
)


def _default_plugin_project() -> Path:
    """Resolve the plugin environment directory via ``bub.home`` (configured by env aliases)."""
    from bub.builtin.cli import _default_project

    return _default_project()


def _ensure_plugin_sandbox(project: Path) -> None:
    """Ensure the AgentSeek plugin sandbox exists and is initialized."""
    from bub.builtin.cli import _build_bub_requirement, _uv

    project.mkdir(parents=True, exist_ok=True)
    if (project / "pyproject.toml").is_file():
        return
    _uv("init", "--bare", "--name", DEFAULT_PLUGIN_SANDBOX, "--app", cwd=project)
    bub_requirement = _build_bub_requirement()
    _uv("add", "--active", "--no-sync", *bub_requirement, cwd=project)


def _build_agentseek_requirement(spec: str) -> str:
    """Resolve a plugin spec, routing ``agentseek-*`` packages directly."""
    from bub.builtin.cli import _build_requirement as _bub_build_requirement

    if spec.startswith(("git@", "https://")) or "/" in spec:
        return _bub_build_requirement(spec)
    name, _, _ = spec.partition("@")
    if name.startswith("agentseek-"):
        return name
    return _bub_build_requirement(spec)


_project_opt = typer.Option(
    default_factory=_default_plugin_project,
    help="Path to the plugin environment directory.",
    envvar="BUB_PROJECT",
    show_envvar=False,
)
_specs_arg = typer.Argument(
    default_factory=list,
    help="Package spec: a git URL, owner/repo, or package name.",
)
_packages_arg = typer.Argument(..., help="Package name to uninstall.")
_packages_optional_arg = typer.Argument(
    default_factory=list,
    help="Package name to update, or omit to update all.",
)

_DEPENDENCY_NAME_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)")


def _resolve_plugin_project(project: Path) -> Path:
    return project.expanduser().resolve()


def _dependency_name(requirement: str) -> str:
    match = _DEPENDENCY_NAME_RE.match(requirement)
    return match.group(1).replace("_", "-").lower() if match else ""


def _is_agentseek_or_bub_dependency(requirement: str) -> bool:
    name = _dependency_name(requirement)
    return name in {"agentseek", "bub"} or name.startswith(("agentseek-", "bub-"))


def _read_project_dependencies(pyproject: Path) -> list[str]:
    try:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        typer.echo(f"Could not read plugin sandbox metadata: {exc}", err=True)
        raise typer.Exit(1) from exc

    dependencies = data.get("project", {}).get("dependencies", [])
    if not isinstance(dependencies, list):
        return []
    return [dependency for dependency in dependencies if isinstance(dependency, str)]


@app.command("list")
def list_plugins(
    project: Path = _project_opt,
) -> None:
    """List AgentSeek/Bub plugin packages declared in the AgentSeek environment."""
    resolved_project = _resolve_plugin_project(project)
    typer.echo(f"Plugin project: {resolved_project}")

    pyproject = resolved_project / "pyproject.toml"
    if not pyproject.is_file():
        typer.echo("Plugin sandbox not found.")
        return

    packages = [
        dependency
        for dependency in _read_project_dependencies(pyproject)
        if _is_agentseek_or_bub_dependency(dependency)
    ]
    if not packages:
        typer.echo("No AgentSeek/Bub plugin packages found.")
        return

    typer.echo("Installed plugin packages:")
    for package in packages:
        typer.echo(f"  - {package}")


@app.command("install")
def install(
    specs: list[str] = _specs_arg,
    project: Path = _project_opt,
) -> None:
    """Install a plugin into the AgentSeek environment, or sync if no specs are given."""
    from bub.builtin.cli import _uv

    _ensure_plugin_sandbox(project)
    if not specs:
        _uv("sync", "--active", "--inexact", cwd=project)
    else:
        _uv("add", "--active", *map(_build_agentseek_requirement, specs), cwd=project)


@app.command("uninstall")
def uninstall(
    packages: list[str] = _packages_arg,
    project: Path = _project_opt,
) -> None:
    """Uninstall a plugin from the AgentSeek environment."""
    from bub.builtin.cli import _uv

    _ensure_plugin_sandbox(project)
    _uv("remove", "--active", *packages, cwd=project)


@app.command("update")
def update(
    packages: list[str] = _packages_optional_arg,
    project: Path = _project_opt,
) -> None:
    """Update selected packages or all packages in the AgentSeek environment."""
    from bub.builtin.cli import _uv

    _ensure_plugin_sandbox(project)
    if not packages:
        _uv("sync", "--active", "--upgrade", "--inexact", cwd=project)
    else:
        package_args: list[str] = []
        for pkg in packages:
            package_args.extend(["--upgrade-package", pkg])
        _uv("sync", "--active", "--inexact", *package_args, cwd=project)
