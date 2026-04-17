#!/usr/bin/env python3
"""CLI wrapper: ensure the configured seekdb or OceanBase database exists."""

from __future__ import annotations

if __name__ == "__main__":
    from bubseek.oceanbase import ensure_database

    ensure_database()
