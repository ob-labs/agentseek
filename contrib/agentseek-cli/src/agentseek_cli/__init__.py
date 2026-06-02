"""Project-lifecycle CLI for AgentSeek.

Exposes a single Typer app that can be invoked two ways:

* As a standalone ``agentseek`` console script (e.g. via ``uvx agentseek-cli``).
* As a Bub plugin that mounts its command groups onto the main ``agentseek``
  framework CLI through the ``register_cli_commands`` hook.
"""

from __future__ import annotations

__all__: list[str] = []
