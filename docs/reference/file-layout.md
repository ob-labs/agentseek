---
title: File layout reference
type: reference
audience: [A2, A4]
runs: no
verified_on: 2026-06-08
sources:
  - src/agentseek/env.py
  - entrypoint.sh
---

# File layout reference

AgentSeek runtime state is local to the workspace unless you override the
environment variables.

| Path | Created by | Purpose |
| --- | --- | --- |
| `.agentseek/` | `agentseek` runtime | AgentSeek runtime home directory. |
| `.agentseek/agentseek-project/` | `agentseek plugin install` | uv project used for plugin dependency resolution. |
| `.agentseek/mcp.json` | user or Docker entrypoint | Default MCP config path. |
| `.agents/skills/` | user | Project-local skills. |
| `.agents/mcp.json` | user | MCP config file — Docker copies this to `.agentseek/mcp.json`. |

## Environment overrides

| Variable | Overrides |
| --- | --- |
| `AGENTSEEK_HOME` / `BUB_HOME` | Runtime home. |
| `AGENTSEEK_PROJECT` / `BUB_PROJECT` | Plugin sandbox path. |
| `AGENTSEEK_MCP_CONFIG_PATH` / `BUB_MCP_CONFIG_PATH` | MCP config path. |

When both prefixes are present, the `BUB_*` value wins. See
[Environment variables](environment.md).
