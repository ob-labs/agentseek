---
title: Reference index
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
---

# Reference

Lookup tables for runtime behaviour. Reference pages mirror facts that live in
the source files listed in each page's `sources:` block. When you see drift,
the source file wins.

| Page | Mirrors |
| --- | --- |
| [Environment variables](environment.md) | `src/agentseek/env.py` — `AGENTSEEK_*` / `BUB_*` aliases. |
| [CLI](cli.md) | `src/agentseek/cli.py` plus `agentseek <subcommand> --help`. |
| [File layout](file-layout.md) | `.agentseek/`, `.agents/`, plugin sandbox. |
| [Packages](packages.md) | `pyproject.toml` — extras, workspace members, contrib entry points. |
| [Templates](templates.md) | `templates/index.json` and each `templates/<framework>/<name>/`. |
| [Docker](docker.md) | `entrypoint.sh`, `docker-compose.yml`, `Dockerfile`. |

## See also

- How-to: [How-to guides](../how-to/index.md)
- Concepts: [Explanation](../explanation/index.md)
