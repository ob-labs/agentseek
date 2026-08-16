"""Regression coverage for the published agentseek-api lifecycle contract script."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

_POSIX_SIGKILL_NUMBER = 9

_BLOCKED_SEPARATE_SESSION_HELPER = """
import json
import os
import pathlib
import signal
import sys
import time

pathlib.Path(sys.argv[1]).write_text(json.dumps({
    "pid": os.getpid(),
    "pgid": os.getpgid(0),
    "parent_pid": os.getppid(),
}), encoding="utf-8")
signal.signal(signal.SIGTERM, lambda *_args: None)
while True:
    time.sleep(0.05)
"""

_PARENT_EXITS_DURING_GRACE_WITH_PRIVATE_HELPER = """
import pathlib
import signal
import subprocess
import sys
import time

helper = pathlib.Path(sys.argv[1])
marker = pathlib.Path(sys.argv[2])
subprocess.Popen(
    [sys.executable, str(helper), str(marker)],
    start_new_session=True,
)

deadline = time.monotonic() + 5
while not marker.is_file():
    if time.monotonic() >= deadline:
        raise TimeoutError("helper did not publish its process marker")
    time.sleep(0.05)

signal.signal(signal.SIGTERM, lambda *_args: sys.exit(0))
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
        os.kill(pid, _POSIX_SIGKILL_NUMBER)
    except ProcessLookupError:
        return


def test_contract_main_rejects_windows_before_helper_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    contract = _load_contract_script()
    monkeypatch.setattr(contract, "os", SimpleNamespace(name="nt"))

    with pytest.raises(RuntimeError) as result:
        contract.main()

    assert str(result.value) == "published agentseek-api lifecycle contract requires POSIX process-group support"


@pytest.mark.skipif(os.name == "nt", reason="the contract timeout fallback requires POSIX process groups")
def test_timeout_reaps_private_helper_when_parent_exits_during_grace(tmp_path: Path) -> None:
    contract = _load_contract_script()
    marker = tmp_path / "helper-process.json"
    helper = tmp_path / "blocked_helper.py"
    helper.write_text(_BLOCKED_SEPARATE_SESSION_HELPER, encoding="utf-8")
    parent = tmp_path / "graceful_parent.py"
    parent.write_text(_PARENT_EXITS_DURING_GRACE_WITH_PRIVATE_HELPER, encoding="utf-8")
    child_pid: int | None = None
    parent_pid: int | None = None
    started = time.monotonic()

    try:
        with pytest.raises(TimeoutError):
            contract._run_agentseek(
                [sys.executable, str(parent), str(helper), str(marker)],
                cwd=tmp_path,
                env=dict(os.environ),
                timeout_seconds=1.0,
                graceful_shutdown_timeout_seconds=1.0,
                helper_process_marker=marker,
                helper_process_group_grace_seconds=0.1,
                fallback_reap_timeout_seconds=1.0,
            )

        elapsed = time.monotonic() - started
        assert elapsed < 4.0, "graceful-parent cleanup exceeded its bounded timeout"
        assert marker.is_file(), "helper process did not publish its private marker"
        observed = json.loads(marker.read_text(encoding="utf-8"))
        child_pid = observed["pid"]
        parent_pid = observed["parent_pid"]
        assert observed["pgid"] == child_pid, "helper did not run in a private process group"
        assert _wait_until(lambda: not _process_is_running(parent_pid)), "parent survived its graceful shutdown"
        assert _wait_until(lambda: not _process_is_running(child_pid)), "helper survived graceful-parent cleanup"
    finally:
        if child_pid is not None:
            _force_stop(child_pid)
        if parent_pid is not None:
            _force_stop(parent_pid)


@pytest.mark.skipif(os.name == "nt", reason="the contract timeout fallback requires POSIX process groups")
def test_timeout_fallback_reaps_actual_agentseek_parent_and_separate_session_helper(tmp_path: Path) -> None:
    contract = _load_contract_script()
    marker = tmp_path / "helper-process.json"
    lifecycle_dir = tmp_path / ".agentseek"
    lifecycle_dir.mkdir()
    helper = tmp_path / "blocked_helper.py"
    helper.write_text(_BLOCKED_SEPARATE_SESSION_HELPER, encoding="utf-8")
    (lifecycle_dir / "lifecycle.toml").write_text(
        "\n".join([
            "version = 2",
            'template = "contract/timeout"',
            'name = "Timeout fallback contract"',
            "",
            "[processes.api]",
            f"command = {json.dumps([sys.executable, str(helper), str(marker)])}",
            'cwd = "."',
        ])
        + "\n",
        encoding="utf-8",
    )
    child_pid: int | None = None
    parent_pid: int | None = None
    started = time.monotonic()

    try:
        with pytest.raises(TimeoutError):
            contract._run_agentseek(
                [sys.executable, "-m", "agentseek", "dev", "--skip-check"],
                cwd=tmp_path,
                env=dict(os.environ),
                timeout_seconds=2.0,
                graceful_shutdown_timeout_seconds=0.2,
                helper_process_marker=marker,
                helper_process_group_grace_seconds=0.1,
                fallback_reap_timeout_seconds=1.0,
            )

        elapsed = time.monotonic() - started
        assert elapsed < 5.0, "fallback cleanup exceeded its bounded timeout"
        assert marker.is_file(), "helper process did not publish its private marker"
        observed = json.loads(marker.read_text(encoding="utf-8"))
        child_pid = observed["pid"]
        parent_pid = observed["parent_pid"]
        assert observed["pgid"] == child_pid, "AgentSeek did not start the helper in a separate session"
        assert _wait_until(lambda: not _process_is_running(parent_pid)), "AgentSeek parent survived timeout fallback"
        assert _wait_until(lambda: not _process_is_running(child_pid)), "helper survived timeout fallback"
    finally:
        if child_pid is not None:
            _force_stop(child_pid)
        if parent_pid is not None:
            _force_stop(parent_pid)
