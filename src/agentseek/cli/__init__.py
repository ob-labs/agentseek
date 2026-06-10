"""Public CLI capabilities for AgentSeek.

The package is intentionally layered:

* :mod:`agentseek.cli.runtime` reimplements Bub's runtime commands with AgentSeek branding.
* :mod:`agentseek.cli.commands` contains AgentSeek-owned command implementations.
* :mod:`agentseek.cli.surface` mounts those capabilities onto the public app.
"""

from __future__ import annotations

from agentseek.cli.runtime import (
    AGENTSEEK_ONBOARD_BANNER,
    AGENTSEEK_ONBOARD_WELCOME,
    agentseek_version,
    apply_agentseek_runtime_command_layout,
    resolve_enabled_channels,
)
from agentseek.cli.surface import (
    AGENTSEEK_CLI_HELP,
    COMMAND_CAPABILITIES,
    CommandCapability,
    iter_command_capabilities,
    mount_agentseek_commands,
)

__all__ = [
    "AGENTSEEK_CLI_HELP",
    "AGENTSEEK_ONBOARD_BANNER",
    "AGENTSEEK_ONBOARD_WELCOME",
    "COMMAND_CAPABILITIES",
    "CommandCapability",
    "agentseek_version",
    "apply_agentseek_runtime_command_layout",
    "iter_command_capabilities",
    "mount_agentseek_commands",
    "resolve_enabled_channels",
]
