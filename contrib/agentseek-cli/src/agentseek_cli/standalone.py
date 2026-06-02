"""Standalone ``agentseek`` entry point used by ``[project.scripts]``.

The script behavior depends on whether the main ``agentseek`` framework is
installed in the same environment:

* **Standalone (uvx)** — framework absent, we run a Typer app containing only
  the command groups owned by ``agentseek-cli``.
* **Monorepo / shared env** — framework present, we defer to
  ``agentseek.__main__.create_cli_app()``. That function loads all Bub
  plugins, including this package's :mod:`agentseek_cli.plugin`, so the
  resulting CLI surface is identical regardless of whether the user resolves
  the ``agentseek`` script from ``agentseek`` or ``agentseek-cli``.

The resolution happens lazily inside :func:`app` so merely importing this
module (e.g. for plugin discovery or tests) stays cheap and never triggers
framework bootstrap.
"""

from __future__ import annotations

from agentseek_cli.app import build_app


def app() -> None:
    """Console-script entry. Resolves the right Typer app on each invocation."""
    try:
        from agentseek.__main__ import create_cli_app
    except ImportError:
        framework_app = build_app()
    else:
        framework_app = create_cli_app()
    framework_app()


__all__ = ["app"]
