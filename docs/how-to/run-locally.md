---
title: How to run agentseek locally
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/run.py
---

# How to run agentseek locally

Use this when you want to run AgentSeek on your machine.

## Prerequisites

- Model credentials configured. See [Configure model](configure-model.md).
- AgentSeek is available as `agentseek`, or installed in the generated project.

## Start a chat

```bash
agentseek chat
```

Use `--chat-id` or `--session-id` only when you need a stable conversation id.

## Run a generated project

Run this from the generated project root:

```bash
uv run agentseek run
```

The command starts the project loop and waits for the frontend. Stop it with
`Ctrl-C`.

If the frontend uses a non-default port, pass it explicitly:

```bash
uv run agentseek run --port 5173
```

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Chat cannot call the model | Provider config is missing or invalid. | Re-check `.env`. |
| `agentseek run` times out | The frontend uses another port. | Pass `--port <n>`. |
| `agentseek run` exits immediately | The directory is not a generated project. | Run it from the generated project root. |

## Related

- [CLI reference](../reference/cli.md)
- [How to run the gateway](run-gateway.md)
- [How to run with Docker Compose](run-with-docker-compose.md)
