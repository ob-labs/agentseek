from __future__ import annotations

from agentseek.branding import (
    AGENTSEEK_ONBOARD_BANNER,
    AGENTSEEK_ONBOARD_WELCOME,
    agentseek_version,
    apply_agentseek_onboard_branding,
)


def test_agentseek_onboard_branding_replaces_bub_banner(monkeypatch) -> None:
    from bub.builtin import cli

    messages = []

    def echo(message=None, *args, **kwargs):
        del args, kwargs
        messages.append(message)

    monkeypatch.setattr(cli, "ONBOARD_BANNER", "Bub v{version}")
    monkeypatch.setattr(cli, "__version__", "bub-version")
    monkeypatch.setattr(cli.typer, "echo", echo)

    apply_agentseek_onboard_branding()

    rendered = cli.ONBOARD_BANNER.format(version=cli.__version__)
    cli.typer.echo("\nWelcome to Bub! Let's get you set up.\n")
    cli.typer.echo("unchanged")

    assert cli.ONBOARD_BANNER == AGENTSEEK_ONBOARD_BANNER
    assert cli.__version__ == agentseek_version()
    assert "AGENTSEEK" in rendered
    assert agentseek_version() in rendered
    assert messages == [AGENTSEEK_ONBOARD_WELCOME, "unchanged"]
