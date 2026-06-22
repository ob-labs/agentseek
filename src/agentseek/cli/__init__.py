"""Public CLI capabilities for AgentSeek.

Two layers:

* :mod:`agentseek.cli.runtime` — orchestrates command layout on top of Bub.
* :mod:`agentseek.cli.commands` — all command implementations.
"""

from __future__ import annotations

from agentseek.cli.banner import AGENTSEEK_BANNER, format_agentseek_banner
from agentseek.cli.runtime import (
    AGENTSEEK_AGENT_MODE_HELP,
    AGENTSEEK_CLI_HELP,
    CliMode,
    agentseek_version,
    apply_agentseek_agent_command_layout,
    apply_agentseek_runtime_command_layout,
    register_app_profile_options,
    resolve_cli_mode,
)

__all__ = [
    "AGENTSEEK_AGENT_MODE_HELP",
    "AGENTSEEK_BANNER",
    "AGENTSEEK_CLI_HELP",
    "CliMode",
    "agentseek_version",
    "apply_agentseek_agent_command_layout",
    "apply_agentseek_runtime_command_layout",
    "format_agentseek_banner",
    "register_app_profile_options",
    "resolve_cli_mode",
]
