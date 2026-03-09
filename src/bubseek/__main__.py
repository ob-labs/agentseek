"""Thin Bub wrapper that forwards environment and CLI arguments via Typer."""

from __future__ import annotations

import sys

import typer

from bubseek.cli import app


def main(argv: list[str] | None = None) -> int:
    """Entry point. Uses sys.argv when argv is None (normal run); otherwise argv (tests)."""
    if argv is not None:
        sys.argv = ["bubseek", *argv]
    try:
        app()
    except typer.Exit as e:
        raise SystemExit(e.exit_code) from e
    return 0  # unreachable (app execve's into bub)


if __name__ == "__main__":
    raise SystemExit(main())
