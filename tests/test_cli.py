from __future__ import annotations

from pathlib import Path

from agentseek.cli import (
    AGENTSEEK_ONBOARD_BANNER,
    AGENTSEEK_ONBOARD_WELCOME,
    agentseek_version,
    apply_agentseek_cli_overrides,
    apply_agentseek_install_project_defaults,
    apply_agentseek_onboard_branding,
)
from agentseek.env import DEFAULT_PLUGIN_SANDBOX


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


def test_apply_agentseek_cli_overrides_runs_onboard_then_install(monkeypatch) -> None:
    order: list[str] = []

    def fake_onboard() -> None:
        order.append("onboard")

    def fake_install() -> None:
        order.append("install")

    monkeypatch.setattr("agentseek.cli.apply_agentseek_onboard_branding", fake_onboard)
    monkeypatch.setattr("agentseek.cli.apply_agentseek_install_project_defaults", fake_install)

    apply_agentseek_cli_overrides()

    assert order == ["onboard", "install"]


def test_install_project_defaults_calls_uv_init_with_agentseek_sandbox_name(monkeypatch, tmp_path) -> None:
    import bub.builtin.cli as bub_cli

    captured: list[list[str]] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        captured.append(list(args))

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)
    monkeypatch.setattr(bub_cli, "_build_bub_requirement", lambda: ["bub"])

    original = bub_cli._ensure_project
    try:
        apply_agentseek_install_project_defaults()
        sandbox = tmp_path / "sandbox"
        sandbox.mkdir()
        bub_cli._ensure_project(sandbox)
    finally:
        object.__setattr__(bub_cli, "_ensure_project", original)

    init_line = next(row for row in captured if row[:2] == ["init", "--bare"])
    assert "--name" in init_line
    assert init_line[init_line.index("--name") + 1] == DEFAULT_PLUGIN_SANDBOX
    add_line = next(row for row in captured if row and row[0] == "add")
    assert add_line[:3] == ["add", "--active", "--no-sync"]
    assert "bub" in add_line


def test_install_project_defaults_skips_uv_when_pyproject_exists(monkeypatch, tmp_path) -> None:
    import bub.builtin.cli as bub_cli

    captured: list[list[str]] = []

    def fake_uv(*args: str, cwd: Path) -> None:
        captured.append(list(args))

    monkeypatch.setattr(bub_cli, "_uv", fake_uv)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\n', encoding="utf-8")

    original = bub_cli._ensure_project
    try:
        apply_agentseek_install_project_defaults()
        bub_cli._ensure_project(tmp_path)
    finally:
        object.__setattr__(bub_cli, "_ensure_project", original)

    assert captured == []
