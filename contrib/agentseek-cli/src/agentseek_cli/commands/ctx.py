"""``agentseek ctx`` — ContextSeek command surface unified under agentseek-cli.

This module hosts both passthrough commands (delegated to ``contextseek``) and
AgentSeek-specific helpers (``init``, ``serve``, ``sync``).
"""

from __future__ import annotations

import importlib
import json
import os
import textwrap
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Annotated, NoReturn

import typer

CTX_PASSTHROUGH_COMMANDS: tuple[str, ...] = (
    "add",
    "retrieve",
    "expand",
    "compact",
    "forget",
    "delete",
    "overview",
    "tools",
    "metrics",
    "dream",
    "feedback",
    "upstream",
    "evidence-chain",
    "chain-confidence",
    "skill-tools",
    "skill-context",
    "skill-import",
    "items",
)

_PLUG_MAP: dict[str, str] = {
    "rag": "contextseek.dataplug.rag:RagPlug",
    "powermem": "contextseek.dataplug.powermem:PowerMemPlug",
    "trace": "contextseek.dataplug.trace:TracePlug",
    "skills": "contextseek.dataplug.skills:SkillsPlug",
}

_PASSTHROUGH = {
    "allow_extra_args": True,
    "ignore_unknown_options": True,
    "help_option_names": [],
}

app = typer.Typer(
    name="ctx",
    help="SeekContext — semantic context layer: write, retrieve, evolve, and serve.",
    add_completion=False,
    no_args_is_help=True,
)


def _run_contextseek(argv: Sequence[str]) -> None:
    """Delegate to contextseek.cli.run_cli(); raise typer.Exit with its exit code."""
    _setup()
    try:
        from contextseek.cli.main import run_cli
    except ModuleNotFoundError:
        _raise_missing_contextseek()
    exit_code = run_cli(list(argv))
    raise typer.Exit(exit_code)


def _passthrough(command_name: str) -> Callable[[typer.Context], None]:
    def _cmd(ctx: typer.Context) -> None:
        _run_contextseek([command_name, *ctx.args])

    _cmd.__name__ = f"ctx_{command_name.replace('-', '_')}"
    _cmd.__doc__ = f"[contextseek] {command_name} — run `agentseek ctx {command_name} --help` for options."
    return _cmd


for _name in CTX_PASSTHROUGH_COMMANDS:
    app.command(_name, context_settings=_PASSTHROUGH)(_passthrough(_name))


@app.command("init")
def cmd_init(
    backend: Annotated[str, typer.Option(help="Storage backend: memory | file | oceanbase")] = "memory",
    path: Annotated[str, typer.Option(help="Root path for file/oceanbase backend")] = ".contextseek/store",
    force: Annotated[bool, typer.Option(help="Overwrite existing config")] = False,
) -> None:
    """Initialize contextseek config and directories in the current project."""
    _setup()
    cwd = Path.cwd()
    ctx_dir = cwd / ".contextseek"
    store_dir = cwd / path

    if ctx_dir.exists() and not force:
        typer.echo(
            ".contextseek/ already exists. Use --force to overwrite.",
            err=True,
        )
        raise typer.Exit(1)

    ctx_dir.mkdir(parents=True, exist_ok=True)
    store_dir.mkdir(parents=True, exist_ok=True)
    typer.echo(f"Created {ctx_dir}")

    _write_env_template(cwd / ".env", backend, path, force)
    _register_mcp(cwd / ".agentseek" / "mcp.json", force)
    typer.echo("contextseek initialized.")


@app.command("serve")
def cmd_serve(
    host: Annotated[str, typer.Option(help="Bind host")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="HTTP port")] = 8001,
    mcp: Annotated[bool, typer.Option(help="Also start MCP SSE server")] = False,
    reload: Annotated[bool, typer.Option(help="Dev mode with auto-reload")] = False,
) -> None:
    """Start the contextseek HTTP API server (and optionally the MCP SSE server)."""
    _setup()
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        msg = "uvicorn is required for `agentseek ctx serve`. Install it with: uv pip install uvicorn"
        raise SystemExit(msg) from exc

    try:
        from contextseek.http.server import create_app  # noqa: F401
    except ModuleNotFoundError as exc:
        msg = "contextseek HTTP server not available. Make sure contextseek[http] is installed."
        raise SystemExit(msg) from exc

    if mcp:
        import threading

        try:
            from contextseek.mcp import create_sse_app
        except ModuleNotFoundError as exc:
            msg = "contextseek MCP server not available. Make sure contextseek[mcp] is installed."
            raise SystemExit(msg) from exc

        mcp_port = port + 1
        mcp_app = create_sse_app()

        def _run_mcp() -> None:
            uvicorn.run(mcp_app, host=host, port=mcp_port, log_level="info")

        thread = threading.Thread(target=_run_mcp, daemon=True)
        thread.start()
        print(f"MCP SSE server started at http://{host}:{mcp_port}")

    uvicorn.run(
        "contextseek.http.server:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@app.command("sync")
def cmd_sync(
    scope: Annotated[str, typer.Option(help="Target scope (tenant/project/agent)")],
    source: Annotated[list[str] | None, typer.Option(help="Source type: rag | powermem | trace | skills")] = None,
    config: Annotated[str, typer.Option(help="DataPlug config file path")] = ".contextseek/sync.yaml",
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Print import count without writing")] = False,
) -> None:
    """Import context from external sources into a scope via DataPlugs."""
    _setup()
    try:
        cs_mod = importlib.import_module("contextseek.client.contextseek")
    except ModuleNotFoundError as exc:
        msg = "contextseek is required. Install with: uv pip install contextseek"
        raise SystemExit(msg) from exc

    ctx = cs_mod.ContextSeek.from_settings()
    sources = source or []

    config_file = Path(config)
    plug_config: dict = {}
    if config_file.exists():
        import yaml  # type: ignore[import-untyped]

        plug_config = yaml.safe_load(config_file.read_text()) or {}

    if not sources:
        typer.echo("No --source specified. Nothing to sync.", err=True)
        raise typer.Exit(1)

    total = 0
    for source_name in sources:
        cls_path = _PLUG_MAP.get(source_name)
        if cls_path is None:
            typer.echo(f"Unknown source '{source_name}'. Valid options: {', '.join(_PLUG_MAP)}", err=True)
            raise typer.Exit(1)

        module_path, cls_name = cls_path.rsplit(":", 1)
        try:
            mod = importlib.import_module(module_path)
            plug_cls = getattr(mod, cls_name)
        except (ModuleNotFoundError, AttributeError) as exc:
            typer.echo(f"Could not load plug for '{source_name}': {exc}", err=True)
            raise typer.Exit(1) from exc

        plug = plug_cls(**plug_config.get(source_name, {}))

        if dry_run:
            count = plug.count(scope=scope)
            typer.echo(f"[dry-run] {source_name}: {count} items would be imported into {scope}")
            total += count
        else:
            imported = ctx.plug(plug, scope=scope)
            imported_count = imported if imported is not None else 0
            typer.echo(f"{source_name}: imported {imported_count} items into {scope}")
            total += imported_count

    if dry_run:
        typer.echo(f"[dry-run] total: {total} items")
    else:
        typer.echo(f"sync complete: {total} items imported into {scope}")


def _setup() -> None:
    _require_contextseek()
    _apply_contextseek_aliases_if_available()


def _require_contextseek() -> None:
    try:
        import contextseek  # noqa: F401
    except ModuleNotFoundError:
        _raise_missing_contextseek()


def _apply_contextseek_aliases_if_available() -> None:
    try:
        from agentseek_contextseek.config import apply_contextseek_env_aliases
    except ModuleNotFoundError:
        return
    apply_contextseek_env_aliases()


def _raise_missing_contextseek() -> NoReturn:
    typer.echo(
        "The `agentseek ctx` commands require `contextseek` in the current environment.\n"
        "Install it with:  uv pip install contextseek\n"
        "Or via extra:     uv pip install 'agentseek[context]'",
        err=True,
    )
    raise typer.Exit(1)


def _write_env_template(env_path: Path, backend: str, path: str, force: bool) -> None:
    base_block = textwrap.dedent(
        f"""\
        # ---------------------------------------------------------------------------
        # ContextSeek (agentseek[context])
        # ---------------------------------------------------------------------------
        # AGENTSEEK_CTX_STORAGE_BACKEND={backend}
        # AGENTSEEK_CTX_STORAGE_PATH={path}
        # AGENTSEEK_CTX_EMBEDDING_PROVIDER=openai
        # AGENTSEEK_CTX_EMBEDDING_MODEL=text-embedding-3-small
        # AGENTSEEK_CTX_EMBEDDING_DIMS=1536
        # AGENTSEEK_CTX_LLM_PROVIDER=openai
        # AGENTSEEK_CTX_LLM_MODEL=gpt-4o-mini
        # AGENTSEEK_CTX_EVOLUTION_ENABLED=true
        # AGENTSEEK_CTX_RETRIEVAL_DEFAULT_K=5
    """
    )

    ob_block = textwrap.dedent(
        """\
        # AGENTSEEK_CTX_OB_HOST=127.0.0.1
        # AGENTSEEK_CTX_OB_PORT=2881
        # AGENTSEEK_CTX_OB_USER=root@test
        # AGENTSEEK_CTX_OB_PASSWORD=
        # AGENTSEEK_CTX_OB_DB_NAME=contextseek
    """
    )

    block = base_block + (ob_block if backend == "oceanbase" else "")

    if env_path.exists():
        existing = env_path.read_text()
        if "AGENTSEEK_CTX_" in existing and not force:
            typer.echo(f"{env_path} already contains AGENTSEEK_CTX_* entries, skipping.")
            return
        env_path.write_text(existing.rstrip() + "\n\n" + block)
    else:
        env_path.write_text(block)

    typer.echo(f"Updated {env_path}")


def _register_mcp(mcp_path: Path, force: bool) -> None:
    entry = {
        "command": "contextseek-mcp-stdio",
        "env": {
            "STORAGE_BACKEND": os.environ.get("AGENTSEEK_CTX_STORAGE_BACKEND", "memory"),
            "OB_HOST": os.environ.get("AGENTSEEK_CTX_OB_HOST", "127.0.0.1"),
        },
    }

    mcp_path.parent.mkdir(parents=True, exist_ok=True)

    if mcp_path.exists():
        try:
            config = json.loads(mcp_path.read_text())
        except json.JSONDecodeError:
            config = {}
        servers = config.setdefault("mcpServers", {})
        if "contextseek" in servers and not force:
            typer.echo(f"{mcp_path} already has 'contextseek' entry, skipping.")
            return
        servers["contextseek"] = entry
    else:
        config = {"mcpServers": {"contextseek": entry}}

    mcp_path.write_text(json.dumps(config, indent=2) + "\n")
    typer.echo(f"Registered contextseek in {mcp_path}")


__all__ = ["CTX_PASSTHROUGH_COMMANDS", "app"]
