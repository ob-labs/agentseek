"""Cross-platform process-tree management for generated development commands."""

from __future__ import annotations

import contextlib
import ctypes
import os
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Any, cast

SHUTDOWN_GRACE_SECONDS = 10.0
SHUTDOWN_POLL_SECONDS = 0.2

_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1


@dataclass
class ManagedProcess:
    """A root process and the platform resource that owns its descendants."""

    process: subprocess.Popen[bytes]
    job: _WindowsJob | None = None
    cleaned: bool = False

    @property
    def pid(self) -> int:
        return self.process.pid

    def poll(self) -> int | None:
        return self.process.poll()

    def wait(self, timeout: float | None = None) -> int:
        return self.process.wait(timeout=timeout)


def spawn_kwargs() -> dict[str, bool | int]:
    """Return ``Popen`` options that isolate a process tree on this platform."""
    if os.name == "nt":
        return {"creationflags": int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))}
    return {"start_new_session": True}


def manage(process: subprocess.Popen[bytes]) -> ManagedProcess:
    """Attach platform-specific tree ownership to a newly spawned process."""
    if os.name != "nt":
        return ManagedProcess(process)
    return ManagedProcess(process, job=_WindowsJob.create(process))


def terminate(managed: ManagedProcess, *, grace_seconds: float = SHUTDOWN_GRACE_SECONDS) -> None:
    """Stop every process owned by *managed*, preserving a graceful timeout."""
    if managed.cleaned:
        return
    try:
        if os.name == "nt":
            _terminate_windows(managed, grace_seconds=grace_seconds)
            return
        _terminate_posix(managed, grace_seconds=grace_seconds)
    finally:
        managed.cleaned = True


def _terminate_posix(managed: ManagedProcess, *, grace_seconds: float) -> None:
    killpg = vars(os)["killpg"]
    sigkill = cast("int", vars(signal)["SIGKILL"])
    try:
        try:
            killpg(managed.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + grace_seconds
        while _process_group_exists(killpg, managed.pid) and time.monotonic() < deadline:
            managed.poll()
            time.sleep(SHUTDOWN_POLL_SECONDS)
        if _process_group_exists(killpg, managed.pid):
            try:
                killpg(managed.pid, sigkill)
            except ProcessLookupError:
                return
    finally:
        _reap_root(managed)


def _reap_root(managed: ManagedProcess) -> None:
    with contextlib.suppress(subprocess.TimeoutExpired):
        managed.wait(timeout=SHUTDOWN_POLL_SECONDS)


def _process_group_exists(killpg: Any, pgid: int) -> bool:
    try:
        killpg(pgid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def _terminate_windows(managed: ManagedProcess, *, grace_seconds: float) -> None:
    job = managed.job
    if job is None:
        _taskkill(managed.pid)
        return
    try:
        if job.active_processes() == 0:
            return
        ctrl_break = getattr(signal, "CTRL_BREAK_EVENT", None)
        if ctrl_break is None or managed.poll() is not None:
            job.terminate()
            return
        try:
            managed.process.send_signal(ctrl_break)
        except (AttributeError, OSError):
            job.terminate()
            return
        deadline = time.monotonic() + grace_seconds
        while job.active_processes() and time.monotonic() < deadline:
            time.sleep(SHUTDOWN_POLL_SECONDS)
        if job.active_processes():
            job.terminate()
    finally:
        job.close()


def _taskkill(pid: int) -> None:
    subprocess.run(  # noqa: S603
        ["taskkill", "/T", "/F", "/PID", str(pid)],  # noqa: S607
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _last_windows_error() -> OSError:
    return vars(ctypes)["WinError"](vars(ctypes)["get_last_error"]())


class _WindowsJob:
    """Minimal Win32 Job Object wrapper; only instantiated on Windows."""

    def __init__(self, handle: int) -> None:
        self._handle = handle

    @classmethod
    def create(cls, process: subprocess.Popen[bytes]) -> _WindowsJob | None:
        job: _WindowsJob | None = None
        try:
            kernel32 = _kernel32()
            handle = kernel32.CreateJobObjectW(None, None)
            if not handle:
                raise _last_windows_error()
            job = cls(int(handle))
            info = _JobObjectExtendedLimitInformation()
            info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not kernel32.SetInformationJobObject(
                job._handle,
                _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
                ctypes.byref(info),
                ctypes.sizeof(info),
            ):
                raise _last_windows_error()
            if not kernel32.AssignProcessToJobObject(job._handle, cast("Any", process)._handle):
                raise _last_windows_error()
        except (AttributeError, OSError):
            if job is not None:
                job.close()
            return None
        else:
            return cast("_WindowsJob", job)

    def active_processes(self) -> int:
        info = _JobObjectBasicAccountingInformation()
        kernel32 = _kernel32()
        if not kernel32.QueryInformationJobObject(
            self._handle,
            _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
            ctypes.byref(info),
            ctypes.sizeof(info),
            None,
        ):
            raise _last_windows_error()
        return int(info.ActiveProcesses)

    def terminate(self) -> None:
        if self._handle and not _kernel32().TerminateJobObject(self._handle, 1):
            raise _last_windows_error()

    def close(self) -> None:
        if self._handle:
            _kernel32().CloseHandle(self._handle)
            self._handle = 0


class _JobObjectBasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JobObjectExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JobObjectBasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _JobObjectBasicAccountingInformation(ctypes.Structure):
    _fields_ = [
        ("TotalUserTime", ctypes.c_longlong),
        ("TotalKernelTime", ctypes.c_longlong),
        ("ThisPeriodTotalUserTime", ctypes.c_longlong),
        ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
        ("TotalPageFaultCount", ctypes.c_uint32),
        ("TotalProcesses", ctypes.c_uint32),
        ("ActiveProcesses", ctypes.c_uint32),
        ("TotalTerminatedProcesses", ctypes.c_uint32),
    ]


def _kernel32() -> Any:
    kernel32 = vars(ctypes)["WinDLL"]("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.SetInformationJobObject.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    kernel32.SetInformationJobObject.restype = ctypes.c_int
    kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel32.AssignProcessToJobObject.restype = ctypes.c_int
    kernel32.QueryInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_void_p,
    ]
    kernel32.QueryInformationJobObject.restype = ctypes.c_int
    kernel32.TerminateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel32.TerminateJobObject.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    return kernel32
