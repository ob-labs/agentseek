from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from contextlib import suppress
from importlib.metadata import version
from pathlib import Path

from agentseek.cli.lifecycle.compatibility import MINIMUM_AGENTSEEK_API_VERSION

_AGENTSEEK_TIMEOUT_SECONDS = 30.0
_AGENTSEEK_GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS = 15.0
_HELPER_PROCESS_GROUP_GRACE_SECONDS = 1.0
_FALLBACK_REAP_TIMEOUT_SECONDS = 5.0
_PROCESS_GROUP_POLL_SECONDS = 0.05
_POSIX_ONLY_CONTRACT_DIAGNOSTIC = "published agentseek-api lifecycle contract requires POSIX process-group support"


def _toml_string(value: str | Path) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def _require_posix_contract_platform() -> None:
    if os.name != "posix":
        raise RuntimeError(_POSIX_ONLY_CONTRACT_DIAGNOSTIC)


def _write_api_capture_helper(root: Path, output: Path, process_marker: Path) -> Path:
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
            "import os",
            "from importlib.metadata import version",
            "from pathlib import Path",
            "from agentseek_api.cli import main",
            f"OUTPUT = Path({_toml_string(output)})",
            f"ENV_FILE = Path({_toml_string(root / '.env')})",
            f"PROCESS_MARKER = Path({_toml_string(process_marker)})",
            "PROCESS_MARKER.write_text(json.dumps({'pid': os.getpid(), 'pgid': os.getpgid(0)}), encoding='utf-8')",
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


def _tracked_posix_process_group(process_marker: Path | None) -> int | None:
    if os.name == "nt" or process_marker is None:
        return None
    try:
        observed = json.loads(process_marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    pid = observed.get("pid") if isinstance(observed, dict) else None
    pgid = observed.get("pgid") if isinstance(observed, dict) else None
    if type(pid) is not int or type(pgid) is not int or pid <= 0 or pid != pgid:
        return None
    try:
        if os.getpgid(pid) != pgid:
            return None
    except (ProcessLookupError, PermissionError):
        return None
    return pgid


def _process_group_exists(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _terminate_tracked_posix_process_group(
    process_marker: Path | None,
    *,
    grace_seconds: float,
    reap_timeout_seconds: float,
) -> None:
    pgid = _tracked_posix_process_group(process_marker)
    if pgid is None:
        return
    with suppress(ProcessLookupError):
        os.killpg(pgid, signal.SIGTERM)
    deadline = time.monotonic() + grace_seconds
    while _process_group_exists(pgid) and time.monotonic() < deadline:
        time.sleep(_PROCESS_GROUP_POLL_SECONDS)
    if not _process_group_exists(pgid):
        return
    with suppress(ProcessLookupError):
        os.killpg(pgid, signal.SIGKILL)
    deadline = time.monotonic() + reap_timeout_seconds
    while _process_group_exists(pgid) and time.monotonic() < deadline:
        time.sleep(_PROCESS_GROUP_POLL_SECONDS)


def _kill_and_reap_agentseek(process: subprocess.Popen[bytes], *, timeout_seconds: float) -> None:
    with suppress(ProcessLookupError):
        process.kill()
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        message = "agentseek dev fallback could not reap its parent"
        raise TimeoutError(message) from None


def _run_agentseek(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: float = _AGENTSEEK_TIMEOUT_SECONDS,
    graceful_shutdown_timeout_seconds: float = _AGENTSEEK_GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS,
    helper_process_marker: Path | None = None,
    helper_process_group_grace_seconds: float = _HELPER_PROCESS_GROUP_GRACE_SECONDS,
    fallback_reap_timeout_seconds: float = _FALLBACK_REAP_TIMEOUT_SECONDS,
) -> int:
    process = subprocess.Popen(  # noqa: S603 - command is constructed by this contract script
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        return process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        if os.name == "nt":
            _kill_and_reap_agentseek(process, timeout_seconds=fallback_reap_timeout_seconds)
            message = "agentseek lifecycle timeout fallback requires POSIX process-group support"
            raise RuntimeError(message) from None
        with suppress(ProcessLookupError):
            process.send_signal(signal.SIGTERM)
        requires_force_kill = False
        try:
            process.wait(timeout=graceful_shutdown_timeout_seconds)
        except subprocess.TimeoutExpired:
            requires_force_kill = True
        _terminate_tracked_posix_process_group(
            helper_process_marker,
            grace_seconds=helper_process_group_grace_seconds,
            reap_timeout_seconds=fallback_reap_timeout_seconds,
        )
        if requires_force_kill:
            _kill_and_reap_agentseek(process, timeout_seconds=fallback_reap_timeout_seconds)
        message = "agentseek dev exceeded the lifecycle-contract timeout"
        raise TimeoutError(message) from None


def main() -> int:
    _require_posix_contract_platform()
    actual_api_version = version("agentseek-api")
    if actual_api_version != MINIMUM_AGENTSEEK_API_VERSION:
        message = f"expected agentseek-api {MINIMUM_AGENTSEEK_API_VERSION}, got {actual_api_version}"
        raise AssertionError(message)

    with tempfile.TemporaryDirectory(prefix="agentseek-api-lifecycle-contract-") as raw_root:
        root = Path(raw_root)
        lifecycle_dir = root / ".agentseek"
        lifecycle_dir.mkdir()
        output = root / "observed.json"
        helper_process_marker = root / ".agentseek-api-helper-process.json"
        helper = _write_api_capture_helper(root, output, helper_process_marker)

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

        returncode = _run_agentseek(
            [sys.executable, "-m", "agentseek", "dev"],
            cwd=root,
            env=launch_environment,
            helper_process_marker=helper_process_marker,
        )
        if returncode != 0:
            message = "agentseek dev failed"
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
