"""Process-wide sandbox backend and cleanup ownership."""

from __future__ import annotations

import atexit

from {{ cookiecutter.project_slug }}.sandbox import create_sandbox_backend

backend, cleanup_sandbox = create_sandbox_backend()
atexit.register(cleanup_sandbox)
