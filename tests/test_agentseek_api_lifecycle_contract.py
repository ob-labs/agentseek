"""Regression coverage for the published agentseek-api lifecycle contract script."""

from __future__ import annotations

import importlib.util
import os
import signal
import sys
import time
from pathlib import Path
from types import ModuleType

import pytest

_PARENT_WITH_REAPED_CHILD = """
import pathlib
import signal
import subprocess
import sys
import time

child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding="utf-8")

def stop(*_args):
    child.terminate()
    child.wait(timeout=5)
    raise SystemExit(0)

signal.signal(signal.SIGTERM, stop)
while True:
    time.sleep(0.05)
"""


def _load_contract_script() -> ModuleType:
    script = Path(__file__).resolve().parents[1] / "scripts" / "check_agentseek_api_lifecycle_contract.py"
    spec = importlib.util.spec_from_file_location("agentseek_api_lifecycle_contract", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _wait_until(predicate, *, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return predicate()


def _process_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _force_stop(pid: int) -> None:
    if not _process_is_running(pid):
        return
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        return


@pytest.mark.skipif(os.name == "nt", reason="the contract's graceful SIGTERM path is POSIX-specific")
def test_timeout_reaps_real_descendant_after_graceful_parent_shutdown(tmp_path: Path) -> None:
    contract = _load_contract_script()
    marker = tmp_path / "child.pid"
    parent = tmp_path / "parent.py"
    parent.write_text(_PARENT_WITH_REAPED_CHILD, encoding="utf-8")
    child_pid: int | None = None

    try:
        with pytest.raises(TimeoutError):
            contract._run_agentseek(
                [sys.executable, str(parent), str(marker)],
                cwd=tmp_path,
                env=dict(os.environ),
                timeout_seconds=1.0,
                graceful_shutdown_timeout_seconds=5.0,
            )

        assert marker.is_file(), "parent process did not publish its descendant PID"
        child_pid = int(marker.read_text(encoding="utf-8"))
        assert _wait_until(lambda: not _process_is_running(child_pid)), "descendant survived timeout cleanup"
    finally:
        if child_pid is not None:
            _force_stop(child_pid)
