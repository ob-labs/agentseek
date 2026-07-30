"""Regression coverage for real development-process supervision."""

from __future__ import annotations

import importlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import pytest
from cookiecutter.main import cookiecutter
from typer.testing import CliRunner

import agentseek.cli.lifecycle.core as lifecycle_core
import agentseek.cli.lifecycle.process_group as process_group
from agentseek.cli.lifecycle.process_group import ManagedProcess, manage, spawn_kwargs, terminate
from tests.cli_commands.helpers import build_command_app

_TREE_SCRIPT = """
import pathlib
import subprocess
import sys
import time

child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding="utf-8")
while True:
    time.sleep(0.1)
"""

_STUBBORN_TREE_SCRIPT = """
import pathlib
import signal
import subprocess
import sys
import time

signal.signal(signal.SIGTERM, lambda *_: None)
if hasattr(signal, "SIGBREAK"):
    signal.signal(signal.SIGBREAK, lambda *_: None)
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
pathlib.Path(sys.argv[1]).write_text(str(child.pid), encoding="utf-8")
while True:
    time.sleep(0.1)
"""

_CLI_TREE_SCRIPT = """
import os
import pathlib
import subprocess
import sys
import time

child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
pathlib.Path(sys.argv[1]).write_text(f"{os.getpid()}:{child.pid}", encoding="utf-8")
while True:
    time.sleep(0.1)
"""

_WAIT_FOR_MARKER_AND_EXIT = """
import pathlib
import sys
import time

marker = pathlib.Path(sys.argv[1])
deadline = time.monotonic() + 5
while not marker.is_file() and time.monotonic() < deadline:
    time.sleep(0.05)
raise SystemExit(7)
"""


def _spawn(command: list[str]) -> subprocess.Popen[bytes]:
    popen = cast("Any", subprocess.Popen)
    return cast("subprocess.Popen[bytes]", popen(command, **spawn_kwargs()))


def _spawn_tree(marker: Path, *, script: str = _TREE_SCRIPT) -> ManagedProcess:
    return manage(_spawn([sys.executable, "-c", script, str(marker)]))


def _wait_until(predicate, *, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.05)
    return predicate()


def _process_is_running(pid: int) -> bool:
    if os.name == "nt":
        result = subprocess.run(  # noqa: S603
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],  # noqa: S607
            check=False,
            capture_output=True,
            text=True,
        )
        return str(pid) in result.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _child_pid(marker: Path) -> int:
    assert _wait_until(marker.is_file), "child process did not publish its PID"
    return int(marker.read_text(encoding="utf-8"))


def _assert_tree_stopped(managed: ManagedProcess, child_pid: int) -> None:
    assert _wait_until(lambda: managed.poll() is not None), "root process survived shutdown"
    assert _wait_until(lambda: not _process_is_running(child_pid)), "child process survived shutdown"


def _force_stop_tree(pid: int) -> None:
    if not _process_is_running(pid):
        return
    if os.name == "nt":
        subprocess.run(  # noqa: S603
            ["taskkill", "/T", "/F", "/PID", str(pid)],  # noqa: S607
            check=False,
            capture_output=True,
        )
        return
    try:
        os.kill(pid, vars(signal)["SIGKILL"])
    except ProcessLookupError:
        return


def test_process_group_probe_treats_permission_error_as_not_running() -> None:
    def forbidden(_pgid: int, _signal: int) -> None:
        raise PermissionError

    assert not process_group._process_group_exists(forbidden, 123)


def test_posix_termination_reaps_a_gracefully_exited_root(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[float] = []

    class ExitedProcess:
        pid = 123

        def poll(self) -> int | None:
            return None

        def wait(self, timeout: float | None = None) -> int:
            calls.append(timeout or 0)
            return 0

    def exited_group(_pgid: int, sig: int) -> None:
        if sig == 0:
            raise ProcessLookupError

    monkeypatch.setitem(vars(process_group.os), "killpg", exited_group)
    monkeypatch.setitem(vars(process_group.signal), "SIGKILL", 9)

    process_group._terminate_posix(cast("ManagedProcess", ExitedProcess()), grace_seconds=0)

    assert calls


def test_terminate_kills_a_real_child_process_tree(tmp_path: Path) -> None:
    managed = _spawn_tree(tmp_path / "child.pid")
    child_pid = _child_pid(tmp_path / "child.pid")
    try:
        assert _process_is_running(child_pid)
        terminate(managed, grace_seconds=0.2)
        _assert_tree_stopped(managed, child_pid)
    finally:
        terminate(managed, grace_seconds=0.0)


def test_terminate_force_stops_a_process_that_ignores_the_graceful_signal(tmp_path: Path) -> None:
    managed = _spawn_tree(tmp_path / "child.pid", script=_STUBBORN_TREE_SCRIPT)
    child_pid = _child_pid(tmp_path / "child.pid")
    try:
        terminate(managed, grace_seconds=0.05)
        _assert_tree_stopped(managed, child_pid)
    finally:
        terminate(managed, grace_seconds=0.0)


def test_wait_for_processes_propagates_exit_code_and_reaps_remaining_trees(tmp_path: Path) -> None:
    marker = tmp_path / "child.pid"
    quick = manage(_spawn([sys.executable, "-c", "raise SystemExit(7)"]))
    long_running = _spawn_tree(marker)
    child_pid = _child_pid(marker)
    try:
        with pytest.raises(SystemExit) as result:
            lifecycle_core._wait_for_processes([quick, long_running])
        assert result.value.code == 7
        _assert_tree_stopped(long_running, child_pid)
    finally:
        terminate(quick, grace_seconds=0.0)
        terminate(long_running, grace_seconds=0.0)


def test_wait_for_processes_ignores_a_second_interrupt_until_every_tree_is_reaped(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _spawn_tree(tmp_path / "first-child.pid", script=_STUBBORN_TREE_SCRIPT)
    second = _spawn_tree(tmp_path / "second-child.pid", script=_STUBBORN_TREE_SCRIPT)
    first_child = _child_pid(tmp_path / "first-child.pid")
    second_child = _child_pid(tmp_path / "second-child.pid")
    monkeypatch.setattr(
        lifecycle_core,
        "_terminate",
        lambda process: terminate(process, grace_seconds=0.1),
    )
    timers = [
        threading.Timer(0.05, lambda: signal.raise_signal(signal.SIGINT)),
        threading.Timer(0.1, lambda: signal.raise_signal(signal.SIGINT)),
    ]
    try:
        for timer in timers:
            timer.start()
        with pytest.raises(SystemExit) as result:
            lifecycle_core._wait_for_processes([first, second])
        assert result.value.code == 0
        _assert_tree_stopped(first, first_child)
        _assert_tree_stopped(second, second_child)
    finally:
        for timer in timers:
            timer.join()
        terminate(first, grace_seconds=0.0)
        terminate(second, grace_seconds=0.0)


def test_dev_reaps_started_processes_when_startup_is_interrupted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = tmp_path / "child.pid"
    started = _spawn_tree(marker)
    child_pid = _child_pid(marker)
    process = cast("Any", type("Process", (), {"command": ("python",), "cwd": "."})())
    project = cast(
        "lifecycle_core.LifecycleProject",
        type(
            "Project",
            (),
            {
                "spec": type("Spec", (), {"processes": {"first": process, "second": process}, "services": {}})(),
            },
        )(),
    )
    calls = 0

    def spawn_then_interrupt(*_args: object, **_kwargs: object) -> ManagedProcess:
        nonlocal calls
        calls += 1
        if calls == 1:
            return started
        raise KeyboardInterrupt

    monkeypatch.setattr(lifecycle_core, "_ensure_required_inputs", lambda _project: None)
    monkeypatch.setattr(lifecycle_core, "_operational_path", lambda *_args, **_kwargs: tmp_path)
    monkeypatch.setattr(lifecycle_core, "_spawn_process", spawn_then_interrupt)
    try:
        with pytest.raises(KeyboardInterrupt):
            lifecycle_core.dev(project, dry_run=False)
        _assert_tree_stopped(started, child_pid)
    finally:
        terminate(started, grace_seconds=0.0)


def test_dev_cli_reaps_remaining_process_tree_and_propagates_exit_code(tmp_path: Path, monkeypatch) -> None:
    marker = tmp_path / "cli-tree.pid"
    spec_dir = tmp_path / ".agentseek"
    spec_dir.mkdir()
    python = Path(sys.executable).as_posix()
    (spec_dir / "lifecycle.toml").write_text(
        "\n".join([
            "version = 2",
            'template = "test/dev-supervision"',
            'name = "Dev supervision"',
            "",
            "[processes.quick]",
            f"command = {json.dumps([python, '-c', _WAIT_FOR_MARKER_AND_EXIT, marker.as_posix()])}",
            "",
            "[processes.long]",
            f"command = {json.dumps([python, '-c', _CLI_TREE_SCRIPT, marker.as_posix()])}",
        ]),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    try:
        result = CliRunner().invoke(build_command_app(), ["dev", "--skip-check"])
        assert result.exit_code == 7, result.stdout + result.stderr
        root_pid, child_pid = map(int, marker.read_text(encoding="utf-8").split(":"))
        assert _wait_until(lambda: not _process_is_running(root_pid)), "root process survived CLI shutdown"
        assert _wait_until(lambda: not _process_is_running(child_pid)), "child process survived CLI shutdown"
    finally:
        if marker.is_file():
            root_pid = int(marker.read_text(encoding="utf-8").split(":", maxsplit=1)[0])
            _force_stop_tree(root_pid)


def test_wait_for_processes_restores_signal_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    class FinishedProcess:
        def poll(self) -> int:
            return 0

    process = cast("ManagedProcess", FinishedProcess())
    previous_int = signal.getsignal(signal.SIGINT)
    previous_term = signal.getsignal(signal.SIGTERM)
    cleaned: list[ManagedProcess] = []
    monkeypatch.setattr(lifecycle_core, "_terminate_all", lambda processes: cleaned.extend(processes))

    with pytest.raises(SystemExit) as result:
        lifecycle_core._wait_for_processes([process])

    assert result.value.code == 0
    assert cleaned == [process]
    assert signal.getsignal(signal.SIGINT) is previous_int
    assert signal.getsignal(signal.SIGTERM) is previous_term


def test_terminate_all_continues_after_one_cleanup_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    first = cast("ManagedProcess", object())
    second = cast("ManagedProcess", object())
    attempted: list[ManagedProcess] = []

    def fail_once(process: ManagedProcess) -> None:
        attempted.append(process)
        if process is first:
            raise OSError

    monkeypatch.setattr(lifecycle_core, "_terminate", fail_once)
    lifecycle_core._terminate_all([first, second])

    assert attempted == [first, second]


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_rendered_langchain_template_reaps_a_real_child_process_tree(tmp_path: Path) -> None:
    template = Path(__file__).parents[2] / "templates" / "langchain" / "default"
    output = tmp_path / "output"
    output.mkdir()
    cookiecutter(str(template), output_dir=str(output), no_input=True)
    generated = next(path for path in output.iterdir() if path.is_dir())
    module = _load_module(
        generated / "src" / generated.name / "process_group.py",
        "rendered_langchain_process_group",
    )
    marker = tmp_path / "template-child.pid"
    managed = module.manage(_spawn([sys.executable, "-c", _TREE_SCRIPT, str(marker)]))
    child_pid = _child_pid(marker)
    try:
        module.terminate(managed, grace_seconds=0.2)
        _assert_tree_stopped(managed, child_pid)
    finally:
        module.terminate(managed, grace_seconds=0.0)


def test_rendered_langchain_template_reaps_gateway_when_frontend_startup_is_interrupted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    template = Path(__file__).parents[2] / "templates" / "langchain" / "default"
    output = tmp_path / "output"
    output.mkdir()
    cookiecutter(str(template), output_dir=str(output), no_input=True)
    generated = next(path for path in output.iterdir() if path.is_dir())
    monkeypatch.syspath_prepend(str(generated / "src"))
    module = importlib.import_module(f"{generated.name}.dev")
    marker = tmp_path / "template-child.pid"
    started = module.manage(_spawn([sys.executable, "-c", _TREE_SCRIPT, str(marker)]))
    child_pid = _child_pid(marker)
    calls = 0

    def spawn_then_interrupt(*_args: object, **_kwargs: object):
        nonlocal calls
        calls += 1
        if calls == 1:
            return started
        raise KeyboardInterrupt

    monkeypatch.setattr(module, "_validate_frontend", lambda _path: None)
    monkeypatch.setattr(module, "_require_binary", lambda _name: "npm")
    monkeypatch.setattr(module, "_spawn", spawn_then_interrupt)
    try:
        with pytest.raises(KeyboardInterrupt):
            module.main()
        _assert_tree_stopped(cast("ManagedProcess", started), child_pid)
    finally:
        module.terminate(started, grace_seconds=0.0)
