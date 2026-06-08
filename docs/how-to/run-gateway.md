---
title: How to run the gateway
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-08
sources:
  - src/agentseek/cli.py
  - entrypoint.sh
---

# How to run the gateway

Use this when you need a long-running process that listens on configured
channels such as Feishu, Telegram, or AG-UI.

## Prerequisites

- Channel plugins installed in the runtime environment.
- Channel credentials present in `.env`.

## Run locally

Show the available options:

```bash
uv run agentseek gateway --help
```

Start one channel:

```bash title="not executed in this run"
uv run agentseek gateway --enable-channel telegram
```

Omit `--enable-channel` to start every registered channel.

## Run in Docker

```bash title="not executed in this run"
docker compose up
```

The repository entrypoint prepares the runtime home and starts
`agentseek gateway` by default. If the mounted workspace contains `startup.sh`,
that script replaces the default gateway command.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `agentseek gateway` is unavailable | Environment is not synced | Run `uv sync`, then retry with `uv run agentseek gateway`. |
| Channel receives no messages | Plugin or credentials missing | Install the plugin and check `.env`. |
| Docker starts the wrong process | `startup.sh` is present | Remove or edit `startup.sh`. |

## Related

- [How to run locally](run-locally.md)
- [How to run with Docker Compose](run-with-docker-compose.md)
- [Docker reference](../reference/docker.md)
