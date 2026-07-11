"""Process-wide sandbox backend and cleanup ownership."""

from __future__ import annotations

import atexit
import threading
from collections.abc import Callable
from typing import Any

from {{ cookiecutter.project_slug }}.sandbox import create_sandbox_backend

_UNINITIALIZED = object()
_lock = threading.Lock()
_backend: Any = _UNINITIALIZED
_provider_cleanup: Callable[[], None] | None = None


def get_backend() -> Any:
    global _backend, _provider_cleanup
    with _lock:
        if _backend is _UNINITIALIZED:
            _backend, _provider_cleanup = create_sandbox_backend()
            atexit.register(cleanup_sandbox)
        return _backend


def cleanup_sandbox() -> None:
    with _lock:
        provider_cleanup = _provider_cleanup
    if provider_cleanup is not None:
        provider_cleanup()
