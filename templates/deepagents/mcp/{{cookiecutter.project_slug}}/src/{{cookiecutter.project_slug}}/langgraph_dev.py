"""Launch LangGraph with a cross-platform argument vector."""

from __future__ import annotations

import os
import shutil
import subprocess


def main() -> int:
    """Run the LangGraph development server with the configured bind host."""
    executable = shutil.which("langgraph")
    if executable is None:
        raise SystemExit("langgraph is unavailable; run `uv sync` first")
    host = os.environ.get("LANGGRAPH_HOST") or "127.0.0.1"
    command = [
        executable,
        "dev",
        "--port",
        "{{ cookiecutter.langgraph_port }}",
        "--no-browser",
        "--host",
        host,
    ]
    return subprocess.call(command)  # noqa: S603 - resolved project dependency with a fixed argv shape


if __name__ == "__main__":
    raise SystemExit(main())
