from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

AGENTSEEK_ONBOARD_BANNER = r"""
    _                    _                 _
   / \   __ _  ___ _ __ | |_ ___  ___  ___| | __
  / _ \ / _` |/ _ \ '_ \| __/ __|/ _ \/ _ \ |/ /
 / ___ \ (_| |  __/ | | | |_\__ \  __/  __/   <
/_/   \_\__, |\___|_| |_|\__|___/\___|\___|_|\_\
        |___/
AGENTSEEK v{version}
""".strip("\n")
AGENTSEEK_ONBOARD_WELCOME = "\nWelcome to agentseek! Let's get you set up.\n"


def apply_agentseek_onboard_branding() -> None:
    """Replace Bub's onboard banner without changing the onboard workflow."""
    from bub.builtin import cli

    cli.ONBOARD_BANNER = AGENTSEEK_ONBOARD_BANNER
    cli.typer.echo = _brand_onboard_echo(cli.typer.echo)
    cli.__version__ = agentseek_version()


def agentseek_version() -> str:
    try:
        return package_version("agentseek")
    except PackageNotFoundError:
        return "0.0.0"


def _brand_onboard_echo(original_echo):
    def echo(message=None, *args, **kwargs):
        if message == "\nWelcome to Bub! Let's get you set up.\n":
            message = AGENTSEEK_ONBOARD_WELCOME
        return original_echo(message, *args, **kwargs)

    return echo
