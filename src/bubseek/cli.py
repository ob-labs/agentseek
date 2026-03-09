"""Typer-based CLI and startup checks for bubseek."""

from __future__ import annotations

import errno
import os
import shutil
import sys
from pathlib import Path
from typing import Annotated

import typer
from dotenv import dotenv_values

from bubseek.config import BubSeekSettings

_CREATE_DB_HINT = """
Please create the database manually, for example:
  mysql -h{host} -P{port} -u{user} -p -e "CREATE DATABASE `{database}` DEFAULT CHARACTER SET utf8mb4"

Or run: uv run python scripts/create-bub-db.py
"""


def _database_exists(host: str, port: int, user: str, password: str, database: str) -> bool:
    import pymysql

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset="utf8mb4",
        )
        conn.close()
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1049:  # Unknown database
            return False
        raise
    except Exception:
        raise
    else:
        return True


def _create_database(host: str, port: int, user: str, password: str, database: str) -> bool:
    import pymysql

    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset="utf8mb4",
        )
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` DEFAULT CHARACTER SET utf8mb4")
        conn.close()
    except Exception:
        return False
    else:
        return True


def ensure_database() -> None:
    """Startup checkpoint: ensure database exists. Prompt to create if missing."""
    settings = BubSeekSettings()
    params = settings.db.mysql_connection_params()
    if params is None:
        return
    host, port, user, password, database = params

    try:
        if _database_exists(host, port, user, password, database):
            return
    except Exception as e:
        typer.echo(f"Cannot connect to {host}:{port}: {e}", err=True)
        typer.echo("Ensure OceanBase/SeekDB is running.", err=True)
        raise typer.Exit(1) from e

    hint = _CREATE_DB_HINT.format(host=host, port=port, user=user, database=database).strip()
    interactive = __import__("sys").stdin.isatty()

    if interactive and not typer.confirm(f"Database {database!r} does not exist. Create it?", default=False):
        typer.echo(hint, err=True)
        raise typer.Exit(1)

    if _create_database(host, port, user, password, database):
        typer.echo(f"Database {database!r} created at {host}:{port}", err=True)
        return

    typer.echo(f"Cannot create database {database!r}.", err=True)
    typer.echo(hint, err=True)
    raise typer.Exit(1)


def forward_environment() -> dict[str, str]:
    """Merge .env into os.environ for bub subprocess."""
    env = dict(os.environ)
    env.update({
        key: value
        for key, value in dotenv_values(Path.cwd() / ".env").items()
        if isinstance(key, str) and isinstance(value, str)
    })
    return env


def _run_bub(args: list[str]) -> None:
    """Replace process with bub, forwarding args and env. Never returns."""
    executable = shutil.which("bub")
    if executable is None:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), "bub")
    env = forward_environment()
    try:
        os.execve(executable, [executable, *(args or ["--help"])], env)  # noqa: S606
    except OSError as e:
        sys.exit(e.errno if e.errno else 1)


app = typer.Typer(
    invoke_without_command=True,
    help="Bubseek: Bub with OceanBase/SeekDB and built-in skills. Forwards all arguments to bub.",
)


@app.callback()
def main(
    args: Annotated[
        list[str] | None,
        typer.Argument(help="Arguments to forward to bub (e.g. chat, gateway, --help)"),
    ] = None,
) -> None:
    """Run bub with bubseek environment and startup checks."""
    ensure_database()
    _run_bub(args if args else ["--help"])
