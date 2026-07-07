"""Feishu gateway launcher for the LangChain template."""

from __future__ import annotations

import os

from .dev import _build_env, _project_root, _spawn, _terminate


def main() -> None:
    root = _project_root()
    env = _build_env(root)

    # macOS system SOCKS proxies can leak into websockets even when shell
    # proxy variables are unset. Force direct websocket connections here.
    env.setdefault("NO_PROXY", "*")
    env.setdefault("no_proxy", "*")

    gateway = _spawn(["bub", "gateway", "--enable-channel", "feishu"], cwd=root, env=env)
    try:
        try:
            raise SystemExit(gateway.wait())
        except KeyboardInterrupt:
            raise SystemExit(0)
    finally:
        _terminate(gateway)
