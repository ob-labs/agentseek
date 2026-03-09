#!/usr/bin/env python3
"""CLI wrapper: ensure bub database exists (delegates to bubseek.cli.ensure_database)."""

from __future__ import annotations

if __name__ == "__main__":
    from bubseek.cli import ensure_database

    ensure_database()
