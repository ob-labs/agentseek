"""Thin Bub wrapper that forwards environment and CLI arguments."""

from __future__ import annotations

import errno
import os
import shutil
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    forwarded_args = args or ["--help"]
    return _forward_to_bub(forwarded_args)


def _forward_to_bub(args: list[str]) -> int:
    executable = shutil.which("bub")
    if executable is None:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), "bub")
    completed = subprocess.run(  # noqa: S603
        [executable, *args],
        check=False,
        env=_forward_environment(),
    )
    return int(completed.returncode)


def _forward_environment() -> dict[str, str]:
    env = dict(os.environ)
    env.update({
        key: value
        for key, value in dotenv_values(Path.cwd() / ".env").items()
        if isinstance(key, str) and isinstance(value, str)
    })
    return env


if __name__ == "__main__":
    raise SystemExit(main())
