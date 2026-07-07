"""Shared AgentSeek CLI banner."""

from __future__ import annotations

AGENTSEEK_BANNER = r"""
    _                    _                 _
   / \   __ _  ___ _ __ | |_ ___  ___  ___| | __
  / _ \ / _` |/ _ \ '_ \| __/ __|/ _ \/ _ \ |/ /
 / ___ \ (_| |  __/ | | | |_\__ \  __/  __/   <
/_/   \_\__, |\___|_| |_|\__|___/\___|\___|_|\_\
        |___/
AGENTSEEK v{version}
""".strip("\n")


def format_agentseek_banner(version: str) -> str:
    return AGENTSEEK_BANNER.format(version=version)


__all__ = ["AGENTSEEK_BANNER", "format_agentseek_banner"]
