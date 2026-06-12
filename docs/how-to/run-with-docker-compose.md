---
title: How to run with Docker Compose
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-12
sources:
  - Dockerfile
  - docker-compose.yml
  - entrypoint.sh
---

# How to run with Docker Compose

Use this when you want to run the gateway in a container.

## Prerequisites

- Docker with the `compose` subcommand.
- A project directory with `docker-compose.yml`.
- A `.env` beside `docker-compose.yml` with at least `AGENTSEEK_MODEL` and
  `AGENTSEEK_API_KEY`.

## Steps

1. Start the container.

   ```bash
   docker compose up --build
   ```

   This starts the container stack and rebuilds the image when needed. Stop it
   with `docker compose down`.

2. Keep runtime files outside the project directory when needed.

   ```bash title=".env"
   AGENTSEEK_DOCKER_WORKSPACE=/srv/agentseek-data
   ```

   Compose mounts that host directory to `/workspace`.

3. Point the container at project-local skills or MCP config when needed.

   ```bash title=".env"
   AGENTSEEK_SKILLS_HOME=/workspace/.agents/skills
   AGENTSEEK_MCP_CONFIG_PATH=/workspace/.agents/mcp.json
   ```

4. Replace the default command when needed.

   Put `startup.sh` in the mounted workspace. The entrypoint executes it
   instead of `agentseek gateway`.

## Rollback

Run `docker compose down` to stop the container. Remove custom values from
`.env` to return to defaults.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Build fails with a frozen lock error. | `uv.lock` is out of sync. | Run `uv sync` or `uv lock`, then rebuild. |
| Data is not persisted where expected. | The workspace mount points at the project directory. | Set `AGENTSEEK_DOCKER_WORKSPACE`. |
| Skills are missing. | `AGENTSEEK_SKILLS_HOME` points elsewhere. | Use `/workspace/.agents/skills`. |
| MCP is not picked up. | `.agents/mcp.json` is missing or the path differs. | Create the file or set `AGENTSEEK_MCP_CONFIG_PATH`. |
| Container starts a custom command. | `startup.sh` exists. | Remove or edit `startup.sh`. |

## Related

- [Environment variables](../reference/environment.md)
- [Build and deploy](build-and-deploy.md)
- [Configure MCP servers](configure-mcp.md)
