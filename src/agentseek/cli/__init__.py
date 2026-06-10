"""Public CLI capabilities for AgentSeek.

Two layers:

* :mod:`agentseek.cli.runtime` — orchestrates command layout on top of Bub.
* :mod:`agentseek.cli.commands` — all command implementations.
"""

from __future__ import annotations

from agentseek.cli.runtime import (
    AGENTSEEK_CLI_HELP,
    AGENTSEEK_ONBOARD_BANNER,
    AGENTSEEK_ONBOARD_WELCOME,
    agentseek_version,
    apply_agentseek_runtime_command_layout,
    resolve_enabled_channels,
)

__all__ = [
    "AGENTSEEK_CLI_HELP",
    "AGENTSEEK_ONBOARD_BANNER",
    "AGENTSEEK_ONBOARD_WELCOME",
    "agentseek_version",
    "apply_agentseek_runtime_command_layout",
    "resolve_enabled_channels",
]
