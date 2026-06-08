---
title: How to run with Docker Compose
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-08
sources:
  - Dockerfile
  - docker-compose.yml
  - entrypoint.sh
---

# How to run with Docker Compose

Use this when you want the AgentSeek gateway, MCP wiring, and skills layout in
a container.

## Prerequisites

- Docker with the `compose` subcommand.
- The repository checked out.
- A `.env` beside `docker-compose.yml` with at least `AGENTSEEK_MODEL` and
  `AGENTSEEK_API_KEY`.

## Start

```bash title="not executed in this run"
docker compose up --build
```

The entrypoint prepares `.agentseek/`, links `.agents/mcp.json` when present,
and starts `agentseek gateway` by default.

## Mount another workspace

```bash title=".env"
AGENTSEEK_DOCKER_WORKSPACE=/srv/agentseek-data
```

Compose mounts that host directory to `/workspace`.

## Replace the default command

Put a `startup.sh` in the mounted workspace. The entrypoint executes it instead
of the default `agentseek gateway`.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Build fails with a frozen lock error | `uv.lock` is out of sync | Run `uv sync` or `uv lock` on the host, then rebuild. |
| Workspace data is not persisted where expected | Default workspace mount points at `.` | Set `AGENTSEEK_DOCKER_WORKSPACE`. |
| Container starts a custom command | `startup.sh` exists | Remove or edit `startup.sh`. |

## Related

- [Docker reference](../reference/docker.md)
- [Environment variables](../reference/environment.md)
- [Build and deploy](build-and-deploy.md)
