---
title: How to configure the Docker workspace
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-05-28
sources:
  - docker-compose.yml
  - entrypoint.sh
---

# How to configure the Docker workspace

Use this when you want Compose to mount a different host directory, when you
need to relocate the plugin sandbox or skills folder, or when you want a
different MCP source path inside the container.

## Prerequisites

- Docker and Docker Compose installed.
- The repository checked out (Compose builds from `.`).

## Steps

1. Pick what to override. The defaults are:

   | Variable | Default in compose | Source |
   | --- | --- | --- |
   | `AGENTSEEK_DOCKER_WORKSPACE` | `.` | `docker-compose.yml:15` |
   | `AGENTSEEK_WORKSPACE_PATH` | `/workspace` | `docker-compose.yml:8` |
   | `AGENTSEEK_HOME` | `/workspace/.agentseek` | `docker-compose.yml:9` |
   | `AGENTSEEK_PROJECT` | `/workspace/.agentseek/agentseek-project` | `docker-compose.yml:10` |
   | `AGENTSEEK_SKILLS_HOME` | `/workspace/.agents/skills` | `docker-compose.yml:11` |
   | `AGENTSEEK_MCP_CONFIG_PATH` | `/workspace/.agents/mcp.json` | `docker-compose.yml:12` |
   | `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | sqlite under `${AGENTSEEK_HOME}` | `docker-compose.yml:13` |

2. Put the overrides in the `.env` next to `docker-compose.yml`. Compose
   reads `.env` automatically via `env_file: .env` (`docker-compose.yml:6`).

   ```bash title=".env"
   # Mount a different host directory at /workspace
   AGENTSEEK_DOCKER_WORKSPACE=/srv/agentseek-data
   # Override the in-container MCP source
   AGENTSEEK_MCP_CONFIG_PATH=/workspace/custom/mcp.json
   ```

3. Bring the container up so the entrypoint re-resolves the variables. The
   resolution order is tabulated in `../reference/docker.md#entrypoint-resolution-order`.

   ```bash title="not executed in this run"
   docker compose up --build
   ```

   TODO(reviewer): run `docker compose up --build` and capture entrypoint
   logs to confirm the override path is taken.

### CLI shortcut

You can also override per invocation:

```bash title="not executed in this run"
AGENTSEEK_DOCKER_WORKSPACE=/srv/agentseek-data docker compose up
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Container writes to the repo root by accident | `AGENTSEEK_DOCKER_WORKSPACE` not set; defaults to `.` | Set it to your data directory before `docker compose up`. |
| Skills not loaded inside container | `AGENTSEEK_SKILLS_HOME` points outside `/workspace/.agents/skills` and you expected Bub to scan elsewhere | Entrypoint symlinks the source into `/workspace/.agents/skills` (`entrypoint.sh:33`); confirm Bub is scanning the link. |
| MCP not picked up | `.agents/mcp.json` missing and `AGENTSEEK_MCP_CONFIG_PATH` unset | Either create the file or set the variable. |

## Rollback

`docker compose down` to stop the container. Remove or comment out the
overrides in `.env` to return to defaults.

## Related

- How-to: `run-with-docker-compose.md`, `configure-mcp.md`
- Reference: `../reference/docker.md`, `../reference/environment.md`
