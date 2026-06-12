---
title: How to run the gateway
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - entrypoint.sh
---

# How to run the gateway

Use this when AgentSeek should listen for channel messages.

## Prerequisites

- The channel plugin is installed in the runtime environment.
- The channel credentials are present in `.env`.

## Run locally

Show the available options:

```bash
agentseek gateway --help
```

Start one channel:

```bash
agentseek gateway --enable-channel telegram
```

Stop the listener with `Ctrl-C`. Omit `--enable-channel` to start every
registered channel.

## Run in Docker

```bash
docker compose up
```

Stop the stack with:

```bash
docker compose down
```

If the mounted workspace contains `startup.sh`, the container runs that script
instead of the default gateway command.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `agentseek gateway` is unavailable | AgentSeek is not installed in this environment. | Install it with `uv tool install agentseek` or add it to the project. |
| The channel receives no messages | Plugin or credentials are missing. | Install the plugin and check `.env`. |
| Docker starts another process | `startup.sh` is present. | Remove or edit `startup.sh`. |

## Related

- [How to run locally](run-locally.md)
- [How to run with Docker Compose](run-with-docker-compose.md)
