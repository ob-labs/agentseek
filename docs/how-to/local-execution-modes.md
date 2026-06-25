---
title: Local execution modes
type: how-to
audience: [A2, A3, A4]
runs: yes
verified_on: 2026-06-25
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/run.py
  - src/agentseek/cli/commands/api.py
  - docs/how-to/run-locally.md
  - docs/how-to/run-gateway.md
  - docs/how-to/run-with-docker-compose.md
---

# Local execution modes

Use this page when you need to choose the right local entry point. It gives the boundaries between the runtime commands, project runner, gateway, API service, and Docker Compose path without repeating the full [CLI reference](../reference/cli.md).

## Choose an entry point

| Goal | Command | Where to run it |
| --- | --- | --- |
| Start an interactive terminal conversation | `agentseek chat` | Any configured AgentSeek environment |
| Send one message and exit | `agentseek turn "message"` | Any configured AgentSeek environment |
| Listen for channel messages | `agentseek gateway` | Runtime environment with channel plugins and credentials |
| Run a generated project locally | `agentseek run` | Generated project root |
| Run a generated project through Compose | `agentseek run --mode compose` | Generated project root with a Compose file |
| Develop the optional API runtime | `agentseek api dev` | Environment with `agentseek-api` installed |

## Runtime commands: `chat`, `turn`, and `gateway`

Use these commands when you want to exercise the AgentSeek runtime directly.

- `agentseek chat` opens an interactive CLI chat session. It is the fastest way to test model configuration and local runtime wiring.
- `agentseek turn "message"` runs one inbound message through the framework pipeline and exits. Use it for scripts, smoke tests, and repeatable command-line checks.
- `agentseek gateway` starts message listeners such as Telegram or other installed channel plugins. Use it when AgentSeek should wait for external messages instead of a terminal prompt.

See [Run locally](run-locally.md) for `chat` and `turn`, and [Run gateway](run-gateway.md) for channel setup.

## Project runner: `agentseek run`

Use `agentseek run` from a generated project root when you want to start the project loop and open the frontend.

In `auto` mode, AgentSeek detects the project layout:

1. If the root contains `docker-compose.yml`, `docker-compose.yaml`, `compose.yml`, or `compose.yaml`, it runs Compose mode.
2. Otherwise, if the root contains `pyproject.toml` plus `app.py`, `main.py`, or a `serve` or `dev` script, it runs Python mode.

Override detection when you already know the intended path:

```bash
uv run agentseek run --mode compose
uv run agentseek run --mode python
```

`agentseek run` also reads `PORT` or `FRONTEND_PORT` from `.env`, probes the frontend host and port, and opens the browser unless you pass `--no-browser`.

## API runtime: `agentseek api dev`

`agentseek api` is a forwarding command group for the optional `agentseek-api` package. Use `agentseek api dev` when you are developing or serving the API runtime itself.

This is different from project-level `agentseek run`:

| Command | Boundary |
| --- | --- |
| `agentseek run` | Starts a generated project from that project directory. |
| `agentseek api dev` | Starts the optional API service exposed by `agentseek-api`. |

If `agentseek-api` is not installed in the current environment, the command reports that dependency requirement instead of starting a project.

## Docker Compose path

There are two Compose paths:

- `docker compose up` starts the Compose stack directly. Use it when you want Docker's normal workflow.
- `agentseek run --mode compose` lets AgentSeek launch Compose, wait for frontend readiness, and optionally open the browser.

Use [Docker Compose](run-with-docker-compose.md) for container setup and environment variables. Use [Build and deploy](build-and-deploy.md) when you need generated deployment artifacts instead of a local development loop.

## Related

- [Run locally](run-locally.md)
- [Run gateway](run-gateway.md)
- [Docker Compose](run-with-docker-compose.md)
- [CLI reference](../reference/cli.md)
