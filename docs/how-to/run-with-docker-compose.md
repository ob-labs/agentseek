---
title: How to run with Docker Compose
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-05-28
sources:
  - Dockerfile
  - docker-compose.yml
  - entrypoint.sh
---

# How to run with Docker Compose

Use this when you want the bundled gateway, MCP wiring, and skills layout
without installing Python locally.

## Prerequisites

- Docker (with the `compose` subcommand) installed.
- The repository checked out (Compose builds from `.`).
- A `.env` next to `docker-compose.yml` with at least an `AGENTSEEK_MODEL`
  and an `AGENTSEEK_API_KEY`. See `configure-model.md`.

## Steps

1. (Optional) Point the workspace mount at a host directory other than the
   repo root:

   ```bash title=".env"
   AGENTSEEK_DOCKER_WORKSPACE=/srv/agentseek-data
   ```

   Compose substitutes this into `${AGENTSEEK_DOCKER_WORKSPACE:-.}:/workspace`
   (`docker-compose.yml:15`).

2. Build the image and start the service:

   ```bash title="not executed in this run"
   docker compose up --build
   ```

   TODO(reviewer): execute against a Docker daemon and capture the
   entrypoint banner.

   The entrypoint exports `BUB_*` and `AGENTSEEK_*` to the values from the
   compose `environment:` block, prepares `.agentseek/` and `.agents/skills`,
   and either runs `${workspace}/startup.sh` if present, or
   `agentseek gateway` by default (`entrypoint.sh:41`, `:45`).

3. Tail the logs in another shell:

   ```bash title="not executed in this run"
   docker compose logs -f
   ```

### Workspace conventions inside the container

| Host (default) | Container | Source |
| --- | --- | --- |
| repo root | `/workspace` | `docker-compose.yml:15`, `entrypoint.sh:5` |
| `.agentseek/` | `/workspace/.agentseek/` | `docker-compose.yml:9` |
| `.agents/skills/` | `/workspace/.agents/skills/` | `docker-compose.yml:11` |
| `.agents/mcp.json` (if present) | linked into `/workspace/.agentseek/mcp.json` | `entrypoint.sh:13`, `:37` |

### Replacing the default command

Put an executable script at `${workspace}/startup.sh`. The entrypoint will
`exec bash startup.sh` instead of `agentseek gateway` (`entrypoint.sh:41`).
Use this to run `agentseek chat` in a one-off container, or a project-defined
binary.

### CLI shortcut

```bash title="not executed in this run"
docker compose up --build       # build + start
docker compose logs -f          # watch
docker compose down             # stop + remove
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `uv sync --frozen --no-dev` fails during build | `uv.lock` out of sync with `pyproject.toml` workspace members | Re-run `uv sync` on the host to refresh the lock; rebuild. |
| Workspace data not persisted | `AGENTSEEK_DOCKER_WORKSPACE` left at default `.` | Mount a real data directory. |

## Rollback

```bash title="not executed in this run"
docker compose down
docker image rm agentseek-app   # if you no longer need the image
```

Remove `.env` entries you added.

## Related

- How-to: `configure-docker-workspace.md`, `build-and-deploy.md`
- Reference: `../reference/docker.md`, `../reference/environment.md`
