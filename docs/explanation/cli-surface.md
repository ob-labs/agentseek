---
title: Command overview
type: explanation
audience: [A1, A2, A4, A5]
runs: no
verified_on: 2026-06-08
sources:
  - README.md
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/surface.py
  - entrypoint.sh
---

# Command overview

All AgentSeek functionality is accessed through the `agentseek` command.
Commands are grouped by what you are trying to do:

| Goal | Commands | Use when |
| --- | --- | --- |
| Project management | `create`, `run`, `build`, `deploy` | You are creating, running, packaging, or deploying a project. |
| Runtime | `chat`, `turn`, `gateway` | You are interacting with the harness. |
| Extensions and services | `plugin`, `ctx`, `skills`, `api`, `mcp` | You are connecting plugins, context, skills, APIs, or MCP servers. |

## Generated projects

Generated projects include `agentseek` as a dependency, so you get the same
commands after `uv sync`. A typical workflow:

```bash
uv run agentseek create langchain/default
cd my-agent
uv sync
uv run agentseek run
```

## Docker Compose

Compose packages the runtime for operators. `entrypoint.sh` prepares the
runtime home and starts `agentseek gateway` unless the workspace provides a
custom startup script.

## Good to know

- Install `agentseek` — there is no separate CLI package.
- Legacy root command forms are not supported; use the grouped commands above.
- Contrib packages are optional runtime extensions, not alternative entry
  points.

## Related

- [CLI reference](../reference/cli.md)
- [Packages reference](../reference/packages.md)
- [How AgentSeek relates to Bub](bub-relationship.md)
- [Where things live](where-things-live.md)
