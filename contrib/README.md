# Contrib

This directory contains plugins for `agentseek`.

Contrib packages remain standard Python packages and should be added through normal dependency management in `pyproject.toml`.

agentseek follows Bub's extension conventions. `AGENTSEEK_*` environment variables and `agentseek-*` packages are aliases for the agentseek distribution namespace; plugin authors should keep Bub-compatible hook and package conventions unless an agentseek-specific alias is needed to avoid namespace conflicts.

## Quick Start

```toml
[project]
dependencies = [
    "bub==0.3.0a1",
    "bub-codex @ git+https://github.com/bubbuild/bub-contrib.git@main#subdirectory=packages/bub-codex",
]
```
