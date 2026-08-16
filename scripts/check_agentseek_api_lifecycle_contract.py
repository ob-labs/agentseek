from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

from agentseek.cli.lifecycle.compatibility import MINIMUM_AGENTSEEK_API_VERSION


def _toml_string(value: str | Path) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _write_api_capture_helper(root: Path, output: Path) -> Path:
    helper = root / "capture_api_environment.py"
    changed_dotenv = (
        "DIRECT_SENTINEL=changed-after-snapshot\n"
        "DEPENDENT_SENTINEL=changed-after-snapshot\n"
        "EXPLICIT_EMPTY=changed-after-snapshot\n"
        "CHILD_ONLY=added-after-snapshot\n"
    )
    helper.write_text(
        "\n".join([
            "from __future__ import annotations",
            "import json",
            "from importlib.metadata import version",
            "from pathlib import Path",
            "from agentseek_api.cli import main",
            f"OUTPUT = Path({_toml_string(output)})",
            f"ENV_FILE = Path({_toml_string(root / '.env')})",
            "def capture(command, *, env, cwd=None):",
            "    OUTPUT.write_text(json.dumps({",
            "        'api_version': version('agentseek-api'),",
            "        'direct': env['DIRECT_SENTINEL'],",
            "        'dependent': env['DEPENDENT_SENTINEL'],",
            "        'explicit_empty_present': 'EXPLICIT_EMPTY' in env,",
            "        'explicit_empty': env['EXPLICIT_EMPTY'],",
            "        'child_only': env['CHILD_ONLY'],",
            "        'graphs': env['AGENTSEEK_GRAPHS'],",
            "    }, sort_keys=True), encoding='utf-8')",
            "    return 0",
            f"ENV_FILE.write_text({_toml_string(changed_dotenv)}, encoding='utf-8')",
            "raise SystemExit(main(['dev', '--config', 'langgraph.json', '--no-reload', '--no-browser'], runner=capture, cwd=Path.cwd()))",
        ])
        + "\n",
        encoding="utf-8",
    )
    return helper


def main() -> int:
    actual_api_version = version("agentseek-api")
    if actual_api_version != MINIMUM_AGENTSEEK_API_VERSION:
        message = f"expected agentseek-api {MINIMUM_AGENTSEEK_API_VERSION}, got {actual_api_version}"
        raise AssertionError(message)

    with tempfile.TemporaryDirectory(prefix="agentseek-api-lifecycle-contract-") as raw_root:
        root = Path(raw_root)
        lifecycle_dir = root / ".agentseek"
        lifecycle_dir.mkdir()
        output = root / "observed.json"
        helper = _write_api_capture_helper(root, output)

        (root / ".env").write_text(
            "DIRECT_SENTINEL=from-dotenv\nDEPENDENT_SENTINEL=${DIRECT_SENTINEL}:resolved-in-file\nEXPLICIT_EMPTY=\n",
            encoding="utf-8",
        )
        (root / "unused.py").write_text("graph = object()\n", encoding="utf-8")
        (root / "langgraph.json").write_text(
            json.dumps({
                "dependencies": [],
                "graphs": {"contract": "./unused.py:graph"},
                "env": ".env",
            }),
            encoding="utf-8",
        )
        (lifecycle_dir / "lifecycle.toml").write_text(
            "\n".join([
                "version = 2",
                'template = "contract/agentseek-api"',
                'name = "Published API contract"',
                'env_file = ".env"',
                "",
                "[env.DIRECT_SENTINEL]",
                "required = true",
                "",
                "[processes.api]",
                f"command = [{_toml_string(sys.executable)}, {_toml_string(helper)}]",
                'cwd = "."',
            ])
            + "\n",
            encoding="utf-8",
        )

        launch_environment = dict(os.environ)
        launch_environment["DIRECT_SENTINEL"] = "from-shell"
        launch_environment.pop("DEPENDENT_SENTINEL", None)
        launch_environment.pop("EXPLICIT_EMPTY", None)
        launch_environment.pop("CHILD_ONLY", None)
        launch_environment.pop("PYTHONPATH", None)

        completed = subprocess.run(
            [sys.executable, "-m", "agentseek", "dev"],
            cwd=root,
            env=launch_environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if completed.returncode != 0:
            message = f"agentseek dev failed ({completed.returncode})\nstdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
            raise AssertionError(message)

        if not output.is_file():
            message = "published API capture runner did not execute"
            raise AssertionError(message)
        observed = json.loads(output.read_text(encoding="utf-8"))
        expected = {
            "api_version": MINIMUM_AGENTSEEK_API_VERSION,
            "child_only": "added-after-snapshot",
            "dependent": "from-dotenv:resolved-in-file",
            "direct": "from-shell",
            "explicit_empty": "",
            "explicit_empty_present": True,
            "graphs": str((root / "langgraph.json").resolve()),
        }
        if observed != expected:
            message = "published API capture did not preserve the lifecycle environment contract"
            raise AssertionError(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
