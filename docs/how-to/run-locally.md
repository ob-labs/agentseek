---
title: How to run agentseek locally
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - contrib/agentseek-cli/README.md
---

# How to run agentseek locally

Use this when you want a quick local loop. agentseek has two local entry
points; pick by intent.

| Goal | Command | Notes |
| --- | --- | --- |
| Sanity-check a chat turn | `agentseek chat` | Single CLI channel + lifecycle channels. Built-in. |
| Run a generated project (template-shaped) | `agentseek run` | Boots a frontend + gateway. Provided by `agentseek-cli` (`pyproject.toml:31`). |

## Prerequisites

- Model and key configured — see `configure-model.md`.
- For `agentseek run`: a project created with `agentseek create` (see
  `../reference/templates.md`) **or** an existing `agentseek-cli`-compatible
  layout in the current directory.

## Option 1 — `agentseek chat`

`agentseek chat` is the built-in CLI channel with lifecycle channels enabled
(`src/agentseek/cli.py:83`). Use it to sanity-check a model / MCP / skills
combination without any frontend.

1. Make sure `.env` has a model and key. See `configure-model.md`.

2. Run a session:

   ```bash title="not executed in this run"
   uv run agentseek chat
   ```

   TODO(reviewer): exercise a real chat turn with a credential during release
   QA. `agentseek chat --help` was confirmed in this run.

3. Optional flags (from `agentseek chat --help`):

   | Flag | Default | Description |
   | --- | --- | --- |
   | `--chat-id` | `local` | Chat id. |
   | `--session-id` | `None` | Optional session id. |

## Option 2 — `agentseek run`

`agentseek run` starts the local project, typically a frontend (Vite) plus a
gateway, and waits for the frontend to become ready.

1. Inside a project directory:

   ```bash title="not executed in this run"
   uv run agentseek run
   ```

2. Tune the launch with the flags below (from `agentseek run --help`):

   | Flag | Default | Description |
   | --- | --- | --- |
   | `--port` | `$PORT` in `.env`, else `3000` | Frontend port. |
   | `--host` | `127.0.0.1` | Host probed for readiness. |
   | `--no-browser` | off | Skip opening the default browser. |
   | `--wait-timeout` | `30` | Seconds to wait for the frontend. |
   | `--mode` | `auto` | One of `auto`, `compose`, `python`. |

`--mode compose` defers to Docker Compose; see
`run-with-docker-compose.md`. `--mode python` runs the project's Python
entry point directly.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `agentseek chat` exits silently after model error | Provider rejected the request | Re-run with the model's debug env, or use `agentseek onboard` to rewrite config. |
| `agentseek run` times out waiting for the frontend | Port mismatch | Pass `--port <n>` matching the frontend's listen port. |
| `agentseek run` exits "not in a project" | `--mode python` selected outside a generated project | Run `agentseek create` first, or switch to `--mode compose`. |

## Rollback

`Ctrl-C` to stop either command. Neither writes persistent state outside
your `.agentseek/` runtime home.

## Related

- How-to: `run-gateway.md`, `run-with-docker-compose.md`,
  `configure-model.md`
- Reference: `../reference/cli.md`
