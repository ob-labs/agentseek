from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def test_agentseek_command_shows_help() -> None:
    command = shutil.which("agentseek")
    assert command is not None

    result = subprocess.run([command, "--help"], capture_output=True, text=True, check=False)  # noqa: S603

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "AGENTSEEK v" in result.stdout


def test_agentseek_version_shows_banner() -> None:
    command = shutil.which("agentseek")
    assert command is not None

    result = subprocess.run([command, "version"], capture_output=True, text=True, check=False)  # noqa: S603

    assert result.returncode == 0
    assert "AGENTSEEK v" in result.stdout


def test_agentseek_invalid_mode_exits_without_traceback() -> None:
    command = shutil.which("agentseek")
    assert command is not None

    result = subprocess.run(  # noqa: S603
        [command, "--mode", "nope", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Unsupported CLI mode: nope" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    ("dotenv_contents", "canary"),
    [
        ("NUL_KEY_CANARY\x00TAIL=value\n", "NUL_KEY_CANARY"),
        ("'EQUALS_KEY_CANARY=TAIL'=value\n", "EQUALS_KEY_CANARY"),
        ("SAFE=value\x00NUL_VALUE_CANARY\n", "NUL_VALUE_CANARY"),
    ],
    ids=["nul-key", "equals-key", "resolved-value"],
)
def test_agentseek_dev_rejects_subprocess_incompatible_dotenv_before_starting_child(
    tmp_path: Path,
    dotenv_contents: str,
    canary: str,
) -> None:
    command = [sys.executable, "-m", "agentseek"]
    spec_dir = tmp_path / ".agentseek"
    spec_dir.mkdir()
    marker = tmp_path / "child.started"
    child_command = [
        sys.executable,
        "-c",
        "from pathlib import Path; Path('child.started').write_text('started', encoding='utf-8')",
    ]
    (spec_dir / "lifecycle.toml").write_text(
        "\n".join([
            "version = 2",
            'template = "test/invalid-dotenv-environment"',
            'name = "Invalid dotenv environment"',
            'env_file = "lifecycle.env"',
            "",
            "[processes.app]",
            f"command = {json.dumps(child_command)}",
        ]),
        encoding="utf-8",
    )
    (tmp_path / "lifecycle.env").write_text(dotenv_contents, encoding="utf-8")

    result = subprocess.run(  # noqa: S603
        [*command, "dev", "--skip-check"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 2
    assert not marker.exists()
    assert "Invalid lifecycle environment." in result.stderr
    assert canary not in output
    assert "\x00" not in output
    assert "\\x00" not in output
    assert "Traceback" not in output


def test_agentseek_task_does_not_inherit_dotenv_secrets(tmp_path: Path) -> None:
    command = shutil.which("agentseek")
    assert command is not None
    spec_dir = tmp_path / ".agentseek"
    spec_dir.mkdir()
    capture_script = tmp_path / "capture_env.py"
    capture_script.write_text(
        """
import json
import os
from pathlib import Path

values = {name: os.environ.get(name) for name in ("AGENTSEEK_SECRET", "BUB_SECRET")}
Path("child-env.json").write_text(json.dumps(values), encoding="utf-8")
""".lstrip(),
        encoding="utf-8",
    )
    (spec_dir / "lifecycle.toml").write_text(
        f"""
version = 1
name = "Environment isolation"
env_file = ".env"

[processes.placeholder]
command = ["{Path(sys.executable).as_posix()}", "-c", "print('unused')"]

[tasks.capture]
command = ["{Path(sys.executable).as_posix()}", "{capture_script.as_posix()}"]
""".lstrip(),
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text("AGENTSEEK_SECRET=dotenv-secret\n", encoding="utf-8")
    parent_environ = os.environ.copy()
    parent_environ.pop("AGENTSEEK_SECRET", None)
    parent_environ.pop("BUB_SECRET", None)

    result = subprocess.run(  # noqa: S603
        [command, "task", "capture"],
        cwd=tmp_path,
        env=parent_environ,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    captured = json.loads((tmp_path / "child-env.json").read_text(encoding="utf-8"))
    assert captured == {"AGENTSEEK_SECRET": None, "BUB_SECRET": None}


def test_agent_mode_only_aliases_launch_environment(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "AGENTSEEK_MODEL=dotenv-model\nAGENTSEEK_SECRET=dotenv-secret\n",
        encoding="utf-8",
    )
    parent_environ = os.environ.copy()
    for name in ("AGENTSEEK_SECRET", "BUB_MODEL", "BUB_SECRET", "PYTHON_DOTENV_DISABLED"):
        parent_environ.pop(name, None)
    parent_environ["AGENTSEEK_MODEL"] = "shell-model"
    probe = """
import json
import os
import sys

sys.argv = ["agentseek", "--mode", "agent"]
import agentseek.__main__  # noqa: F401

print(json.dumps({
    "AGENTSEEK_SECRET": os.environ.get("AGENTSEEK_SECRET"),
    "BUB_MODEL": os.environ.get("BUB_MODEL"),
    "BUB_SECRET": os.environ.get("BUB_SECRET"),
    "PYTHON_DOTENV_DISABLED": os.environ.get("PYTHON_DOTENV_DISABLED"),
}))
""".lstrip()

    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", probe],
        cwd=tmp_path,
        env=parent_environ,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {
        "AGENTSEEK_SECRET": None,
        "BUB_MODEL": "shell-model",
        "BUB_SECRET": None,
        "PYTHON_DOTENV_DISABLED": None,
    }


def test_logfire_console_config_maps_bool_to_runtime_config() -> None:
    from logfire import ConsoleOptions

    import agentseek.__main__ as entrypoint

    disabled = entrypoint._logfire_console_config(False)
    enabled = entrypoint._logfire_console_config(True)

    assert disabled is False
    assert isinstance(enabled, ConsoleOptions)
    assert enabled.verbose is False


def test_agent_mode_applies_process_environment_aliases(monkeypatch, tmp_path: Path) -> None:
    import bub.framework

    import agentseek.__main__ as entrypoint
    from agentseek.env import DEFAULT_AGENTSEEK_CONFIG, DEFAULT_PLUGIN_SANDBOX

    agentseek_home = tmp_path / "agentseek-home"
    monkeypatch.setenv("AGENTSEEK_HOME", str(agentseek_home))
    monkeypatch.delenv("BUB_HOME", raising=False)
    monkeypatch.delenv("BUB_PROJECT", raising=False)
    captured: dict[str, object] = {}

    class FakeBubFramework:
        def __init__(self, config_file: Path) -> None:
            captured["config_file"] = config_file

        def load_hooks(self) -> None:
            captured["hooks_loaded"] = True

    monkeypatch.setattr(bub.framework, "BubFramework", FakeBubFramework)

    entrypoint._create_agent_cli_app()

    assert captured == {
        "config_file": (agentseek_home / DEFAULT_AGENTSEEK_CONFIG).resolve(),
        "hooks_loaded": True,
    }
    assert Path(os.environ["BUB_HOME"]) == agentseek_home
    assert Path(os.environ["BUB_PROJECT"]) == agentseek_home / DEFAULT_PLUGIN_SANDBOX
