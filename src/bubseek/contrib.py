"""Helpers for configured contrib metadata."""

from __future__ import annotations

from typing import Any

from bubseek.config import configured_contrib_packages, load_config


def load_bubseek_config() -> dict[str, Any]:
    """Load `bubseek.toml`."""
    return load_config()


def default_contrib_packages() -> list[str]:
    """Return configured contrib package names from `bubseek.toml`."""
    return configured_contrib_packages(load_bubseek_config())
