---
title: CLI surface
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

# CLI surface

AgentSeek now has one public CLI entry point: `agentseek`.

The design keeps one command name while separating command groups by job:

| Job | Commands | Use when |
| --- | --- | --- |
| Project management | `create`, `run`, `build`, `deploy` | You are creating, running, packaging, or deploying a project. |
| Runtime | `chat`, `turn`, `gateway` | You are interacting with the harness. |
| Extension and services | `plugin`, `ctx`, `skills`, `api`, `mcp` | You are connecting plugins, context, skills, APIs, or MCP servers. |

This shape matches the way AgentSeek is used in practice: project management
is important enough to be first-class, but it should not require a
separate package or a separate command name. The runtime stays equally visible
because the same package is also an executable harness.

## Why command groups are separated

- `create / run / build / deploy` are project operations. They can work before a
  long-running harness is started.
- `chat / turn / gateway` are runtime operations. They execute the harness.
- `plugin / ctx / skills / api / mcp` connect the runtime to optional services
  and tools.

This avoids ambiguous root commands. Bub's root `run` becomes `agentseek turn`,
and root plugin mutation commands move under `agentseek plugin`.

## Generated projects

Generated projects depend on `agentseek` and therefore receive the same command
surface after `uv sync`. The normal loop is:

```bash
uv run agentseek create langchain/default
cd my-agent
uv sync
uv run agentseek run
```

## Docker Compose

Compose packages the runtime for operators. `entrypoint.sh` prepares the
runtime home, maps `AGENTSEEK_*` variables to Bub, and starts `agentseek
gateway` unless the workspace provides a custom startup script.

## Consequences

- Install and document `agentseek`, not a companion CLI package.
- Old root forms are intentionally invalid; do not rely on aliases.
- Contrib packages remain optional runtime extensions, not alternative entry
  points.

## Related

- [CLI reference](../reference/cli.md)
- [Packages reference](../reference/packages.md)
- [How AgentSeek relates to Bub](bub-relationship.md)
- [Where things live](where-things-live.md)
