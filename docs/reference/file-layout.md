---
title: File layout reference
type: reference
audience: [A2, A4]
runs: no
verified_on: 2026-06-12
sources:
  - src/agentseek/env.py
  - entrypoint.sh
---

# File layout reference

## Runtime paths

| Path | Created by | Purpose |
| --- | --- | --- |
| `.agentseek/` | AgentSeek runtime | Default runtime home. |
| `.agentseek/agentseek-project/` | `agentseek plugin install` | uv project used for plugin dependency resolution. |
| `.agentseek/mcp.json` | User or Docker entrypoint | Default MCP config path. |
| `.agents/skills/` | User | Project-local skills. |
| `.agents/mcp.json` | User | Workspace MCP config that Docker links to the runtime path. |

## Overrides

| Variable | Overrides |
| --- | --- |
| `AGENTSEEK_HOME`, `BUB_HOME` | Runtime home. |
| `AGENTSEEK_PROJECT`, `BUB_PROJECT` | Plugin environment path. |
| `AGENTSEEK_MCP_CONFIG_PATH`, `BUB_MCP_CONFIG_PATH` | MCP config path. |
