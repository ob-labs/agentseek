from __future__ import annotations

from agentseek.env import apply_agentseek_env_aliases

apply_agentseek_env_aliases()

from bub.__main__ import app  # noqa: E402

__all__ = ["app"]


if __name__ == "__main__":
    app()
