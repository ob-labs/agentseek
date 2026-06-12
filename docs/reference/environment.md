---
title: Environment variables reference
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-06-12
sources:
  - src/agentseek/env.py
  - entrypoint.sh
  - docker-compose.yml
---

# Environment variables reference

## Namespaces

| Namespace | Role |
| --- | --- |
| `AGENTSEEK_*` | Project-facing aliases. |
| `BUB_*` | Runtime variables consumed by Bub. |

## Defaults

| Variable | Default |
| --- | --- |
| `BUB_HOME` | `${cwd}/.agentseek` |
| `BUB_PROJECT` | `${BUB_HOME}/agentseek-project` |

## Alias mapping

| `AGENTSEEK_*` | `BUB_*` | Description |
| --- | --- | --- |
| `AGENTSEEK_HOME` | `BUB_HOME` | Runtime home directory. |
| `AGENTSEEK_PROJECT` | `BUB_PROJECT` | Plugin environment path. |
| `AGENTSEEK_WORKSPACE_PATH` | `BUB_WORKSPACE_PATH` | Workspace root. |
| `AGENTSEEK_SKILLS_HOME` | `BUB_SKILLS_HOME` | Skills directory. |
| `AGENTSEEK_MCP_CONFIG_PATH` | `BUB_MCP_CONFIG_PATH` | MCP config path. |
| `AGENTSEEK_MODEL` | `BUB_MODEL` | Model identifier. |
| `AGENTSEEK_API_KEY` | `BUB_API_KEY` | Provider API key. |
| `AGENTSEEK_API_BASE` | `BUB_API_BASE` | OpenAI-compatible base URL. |
| `AGENTSEEK_MAX_STEPS` | `BUB_MAX_STEPS` | Model/tool loop limit. |
| `AGENTSEEK_MAX_TOKENS` | `BUB_MAX_TOKENS` | Response token budget. |
| `AGENTSEEK_MODEL_TIMEOUT_SECONDS` | `BUB_MODEL_TIMEOUT_SECONDS` | Model request timeout. |

## AgentSeek-only settings

| Variable | Type | Default | Description |
| --- | --- | --- | --- |
| `AGENTSEEK_CONSOLE` | boolean | `false` | Enable Logfire console output. |

## Docker variables

| Variable | Compose default | Description |
| --- | --- | --- |
| `AGENTSEEK_DOCKER_WORKSPACE` | `.` | Host workspace mounted into the container. |
| `AGENTSEEK_WORKSPACE_PATH` | `/workspace` | Workspace path inside the container. |
| `AGENTSEEK_HOME` | `/workspace/.agentseek` | Runtime home inside the container. |
| `AGENTSEEK_PROJECT` | `/workspace/.agentseek/agentseek-project` | Plugin environment inside the container. |
| `AGENTSEEK_SKILLS_HOME` | `/workspace/.agents/skills` | Skills directory inside the container. |
| `AGENTSEEK_MCP_CONFIG_PATH` | `/workspace/.agents/mcp.json` | MCP config path inside the container. |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | `sqlite+pysqlite:////workspace/.agentseek/agentseek-tapes.db` | Default SQLAlchemy tape-store URL. |

## Precedence

| Rank | Source |
| --- | --- |
| 1 | Process environment `BUB_*` value. |
| 2 | Process environment `AGENTSEEK_*` value, aliased to `BUB_*`. |
| 3 | `.env` `AGENTSEEK_*` value, aliased to `BUB_*`. |
| 4 | AgentSeek defaults for `BUB_HOME` and `BUB_PROJECT`. |

## `.env`

| Behavior | Value |
| --- | --- |
| File path | `.env` in the current working directory. |
| Empty values | Ignored. |
| `.env` `BUB_*` values | Not imported by the alias probe. |
