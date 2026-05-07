# Contrib

This directory contains contrib packages maintained in the `agentseek` monorepo.

Most of these packages are exposed to the runtime as Bub plugins through
`[project.entry-points.bub]`. In other words:

- `agentseek` names the distribution, monorepo, and user-facing packaging namespace
- `Bub` names the plugin model, hook contracts, entry-point group, and config section semantics

Contrib packages remain standard Python packages and should be added through normal dependency
management in `pyproject.toml`.

agentseek follows Bub's extension conventions. `AGENTSEEK_*` environment variables and
`agentseek-*` packages belong to the agentseek distribution namespace; plugin authors should keep
Bub-compatible hooks, entry points, and config behavior unless an agentseek-specific alias is
needed to avoid namespace conflicts.

## Quick Start

```toml
[project]
dependencies = [
    "agentseek-schedule-sqlalchemy",
]
```
