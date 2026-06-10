---
title: How to run agentseek locally
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-06-08
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/dev.py
---

# How to run agentseek locally

Use this when you want a quick local loop from this repository or from a
generated project.

## Prerequisites

- Model credentials configured. See [Configure model](configure-model.md).
- A synced environment: `uv sync` in this repository or inside a generated project.

## Chat with the harness

```bash title="not executed in this run"
uv run agentseek chat
```

Optional flags:

| Flag | Default | Description |
| --- | --- | --- |
| `--chat-id` | `local` | Chat id. |
| `--session-id` | `None` | Optional session id. |

## Run a generated project

Inside a project created by `agentseek create`:

```bash title="not executed in this run"
uv run agentseek run
```

Common flags:

| Flag | Default | Description |
| --- | --- | --- |
| `--port` | `$PORT` or `3000` | Frontend port. |
| `--host` | `127.0.0.1` | Readiness host. |
| `--no-browser` | off | Do not open the browser. |
| `--wait-timeout` | `30` | Seconds to wait for frontend readiness. |
| `--mode` | `auto` | One of `auto`, `compose`, `python`. |

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `agentseek chat` cannot call the model | Provider config missing or invalid | Re-check `.env` or run `agentseek onboard`. |
| `agentseek run` times out | Frontend listens on another port | Pass `--port <n>`. |
| `agentseek run` exits outside a project | No generated project layout found | Run `agentseek create` first or use `agentseek chat`. |

## Related

- [CLI reference](../reference/cli.md)
- [How to run the gateway](run-gateway.md)
- [How to run with Docker Compose](run-with-docker-compose.md)
