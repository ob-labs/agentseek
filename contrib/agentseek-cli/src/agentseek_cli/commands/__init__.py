"""Top-level command groups for the AgentSeek CLI.

Each module here exposes a ``app: typer.Typer`` Typer subapp with a fixed
``name`` matching the user-facing command. :mod:`agentseek_cli.app` mounts
them in declaration order.
"""

from __future__ import annotations

__all__: list[str] = []
