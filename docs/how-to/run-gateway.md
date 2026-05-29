---
title: How to run the gateway
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - entrypoint.sh
  - docs/index.md
---

# How to run the gateway

Use this when you need a **long-running** process that listens on channels
(Feishu, Telegram, AG-UI, …). `agentseek gateway` belongs to the **harness**
package, so this page assumes Path B: this repo after `uv sync`, a generated
project after `uv sync`, or Docker Compose wrapping that same harness.

## Prerequisites

- The channel plugins you want enabled are installed in the runtime env
  (e.g. `bub-feishu` ships with agentseek by default — `pyproject.toml:20`).
- Channel credentials in `.env`.

## Steps

1. Enable the channels you need. By default, `agentseek gateway` starts every
   registered channel.

   ```bash
   uv run agentseek gateway --help
   ```

   ```text title="output"
   Usage: agentseek gateway [OPTIONS]

    Start message listeners(like telegram).

   ╭─ Options ─────────────────────────────────────────────╮
   │ --enable-channel  TEXT  Channels to enable for CLI    │
   │                         (default: all)                │
   │ --help                  Show this message and exit.   │
   ╰───────────────────────────────────────────────────────╯
   ```

2. Start the gateway:

   ```bash title="not executed in this run"
   uv run agentseek gateway --enable-channel telegram
   ```

3. To run inside Docker, just bring the stack up — `entrypoint.sh:45` execs
   `agentseek gateway` by default:

   ```bash title="not executed in this run"
   docker compose up
   ```

   To run something other than `agentseek gateway` under the same entrypoint,
   put a `startup.sh` in the workspace; the entrypoint will `exec bash`
   it instead (`entrypoint.sh:41`).

### Scope

This command is part of the harness runtime CLI. Path A with only
`agentseek-cli` installed does not provide it. There is no separate embedding
API for the gateway.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `agentseek gateway` not found | You are on Path A with only `agentseek-cli` installed | Use a harness environment, or Docker Compose on top of it. |
| Channel never receives messages | Plugin missing in the runtime env | `uv run agentseek install <plugin>` to add it to the sandbox. |
| Gateway exits immediately | Channel credentials missing | Inspect the log for the channel name; add the credential to `.env`. |
| Multiple gateways race in Docker | `startup.sh` and the default entrypoint both ran | Pick one; `startup.sh` replaces, it does not chain. |

## Rollback

`Ctrl-C` to stop. In Docker: `docker compose down`. There is no persistent
state beyond what each channel plugin stores (e.g. cursor files).

## Related

- How-to: `run-locally.md`, `run-with-docker-compose.md`,
  `configure-docker-workspace.md`
- Reference: `../reference/cli.md`, `../reference/docker.md`
