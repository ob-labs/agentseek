---
title: Docker reference
type: reference
audience: [A4]
runs: no
verified_on: 2026-05-28
sources:
  - Dockerfile
  - entrypoint.sh
  - docker-compose.yml
---

# Docker reference

This page mirrors `Dockerfile`, `entrypoint.sh`, and `docker-compose.yml` at
the verification date. For task instructions, see
`../how-to/run-with-docker-compose.md`.

## Image

| Property | Value | Source |
| --- | --- | --- |
| Base image | `python:3.12-slim` | `Dockerfile:2` |
| `uv` source | `ghcr.io/astral-sh/uv:latest` (copied to `/bin/uv`) | `Dockerfile:3` |
| Extra apt packages | `tini`, `git` | `Dockerfile:6` |
| Workdir (build) | `/app` | `Dockerfile:11` |
| Workdir (run) | `/workspace` | `Dockerfile:25` |
| Build env | `UV_LINK_MODE=copy`, `UV_COMPILE_BYTECODE=1`, `PYTHONUNBUFFERED=1` | `Dockerfile:17` |
| Install command | `uv sync --frozen --no-dev` | `Dockerfile:21` |
| Entrypoint | `/usr/bin/tini --` | `Dockerfile:27` |
| Default CMD | `/app/entrypoint.sh` | `Dockerfile:28` |

The whole tree is copied to `/app` before `uv sync` because uv workspace
members under `contrib/` must exist for the lockfile to resolve.

## Compose service

`docker-compose.yml` defines a single `app` service:

| Property | Value | Source |
| --- | --- | --- |
| Build context | `.` | `docker-compose.yml:3` |
| `env_file` | `.env` | `docker-compose.yml:6` |
| Volume mount | `${AGENTSEEK_DOCKER_WORKSPACE:-.}:/workspace` | `docker-compose.yml:15` |
| Restart policy | `unless-stopped` | `docker-compose.yml:16` |

## Compose `environment` block

| Variable | Value | Source |
| --- | --- | --- |
| `AGENTSEEK_WORKSPACE_PATH` | `/workspace` | `docker-compose.yml:8` |
| `AGENTSEEK_HOME` | `/workspace/.agentseek` | `docker-compose.yml:9` |
| `AGENTSEEK_PROJECT` | `/workspace/.agentseek/agentseek-project` | `docker-compose.yml:10` |
| `AGENTSEEK_SKILLS_HOME` | `/workspace/.agents/skills` | `docker-compose.yml:11` |
| `AGENTSEEK_MCP_CONFIG_PATH` | `/workspace/.agents/mcp.json` | `docker-compose.yml:12` |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | `sqlite+pysqlite:////workspace/.agentseek/agentseek-tapes.db` (overridable) | `docker-compose.yml:13` |

## Entrypoint resolution order

`entrypoint.sh` resolves each variable in this order; the first non-empty
value wins:

| Step | Variable | Order checked (first non-empty wins) | Source |
| --- | --- | --- | --- |
| 1 | `workspace_path` | `BUB_WORKSPACE_PATH` → `AGENTSEEK_WORKSPACE_PATH` → `/workspace` | `entrypoint.sh:5` |
| 2 | `agentseek_home` | `BUB_HOME` → `AGENTSEEK_HOME` → `${workspace_path}/.agentseek` | `entrypoint.sh:6` |
| 3 | `skills_target` | `${workspace_path}/.agents/skills` (fixed) | `entrypoint.sh:7` |
| 4 | `skills_home` | `BUB_SKILLS_HOME` → `AGENTSEEK_SKILLS_HOME` → `${skills_target}` | `entrypoint.sh:8` |
| 5 | `project_home` | `BUB_PROJECT` → `AGENTSEEK_PROJECT` → `${agentseek_home}/agentseek-project` | `entrypoint.sh:9` |
| 6 | `mcp_config_target` | `${agentseek_home}/mcp.json` (fixed) | `entrypoint.sh:10` |
| 7 | `mcp_config_source` | `BUB_MCP_CONFIG_PATH` → `AGENTSEEK_MCP_CONFIG_PATH` → `${workspace_path}/.agents/mcp.json` if that file exists | `entrypoint.sh:11`, `:13` |

All resolved values are then re-exported as both `BUB_*` and `AGENTSEEK_*`
(`entrypoint.sh:17`).

## Filesystem actions

| Action | Condition | Source |
| --- | --- | --- |
| `mkdir -p ${BUB_HOME} ${BUB_PROJECT} ${workspace_path}/.agents` | always | `entrypoint.sh:28` |
| `mkdir -p ${skills_target}` | when `skills_home == skills_target` | `entrypoint.sh:30` |
| `mkdir -p ${skills_home}; ln -sfn ${skills_home} ${skills_target}` | when `skills_home != skills_target` | `entrypoint.sh:33` |
| `ln -sfn ${mcp_config_source} ${mcp_config_target}` | when source is set, exists, and differs from target | `entrypoint.sh:37` |

## Launch order

1. If `${workspace_path}/startup.sh` exists, `exec bash` it (`entrypoint.sh:41`).
2. Otherwise `exec /app/.venv/bin/agentseek gateway` (`entrypoint.sh:45`).

A user-supplied `startup.sh` therefore fully replaces the default `agentseek
gateway` invocation.

## See also

- How-to: `../how-to/run-with-docker-compose.md`,
  `../how-to/configure-docker-workspace.md`
- Reference: `environment.md`, `file-layout.md`
