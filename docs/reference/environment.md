---
title: Environment variables reference
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - entrypoint.sh
  - docker-compose.yml
---

# Environment variables reference

agentseek reads its runtime configuration from two parallel namespaces:

- `AGENTSEEK_*` — the project-facing names.
- `BUB_*` — the upstream Bub names that the runtime ultimately consumes.

At startup, `apply_agentseek_env_aliases()` copies every `AGENTSEEK_<NAME>`
into the matching `BUB_<NAME>` slot **only when `BUB_<NAME>` is not already
set** (`setdefault`). See `src/agentseek/env.py:56`.

## Defaults set by `apply_agentseek_env_aliases`

| Variable | Default | Defined in |
| --- | --- | --- |
| `BUB_HOME` | `Path.cwd() / ".agentseek"` | `src/agentseek/env.py:70`, `:86` |
| `BUB_PROJECT` | `${BUB_HOME}/agentseek-project` | `src/agentseek/env.py:72` |

Both defaults are applied with `setdefault`, so explicit values win.

## Alias mapping

| `AGENTSEEK_*` name | Maps to `BUB_*` | Notes |
| --- | --- | --- |
| `AGENTSEEK_HOME` | `BUB_HOME` | Runtime home directory. |
| `AGENTSEEK_PROJECT` | `BUB_PROJECT` | Plugin sandbox used by `agentseek install`. |
| `AGENTSEEK_WORKSPACE_PATH` | `BUB_WORKSPACE_PATH` | Workspace root, used by the Docker entrypoint (`entrypoint.sh:5`). |
| `AGENTSEEK_SKILLS_HOME` | `BUB_SKILLS_HOME` | Skill source directory (`entrypoint.sh:8`). |
| `AGENTSEEK_MCP_CONFIG_PATH` | `BUB_MCP_CONFIG_PATH` | MCP config file path. |
| `AGENTSEEK_MODEL` | `BUB_MODEL` | Model identifier (e.g. `openrouter:free`). |
| `AGENTSEEK_API_KEY` | `BUB_API_KEY` | API key for the configured provider. |
| `AGENTSEEK_API_BASE` | `BUB_API_BASE` | OpenAI-compatible base URL. |
| `AGENTSEEK_MAX_STEPS` | `BUB_MAX_STEPS` | Model/tool loop limit. |
| `AGENTSEEK_MAX_TOKENS` | `BUB_MAX_TOKENS` | Response token budget. |
| `AGENTSEEK_MODEL_TIMEOUT_SECONDS` | `BUB_MODEL_TIMEOUT_SECONDS` | Model request timeout. |

The mapping is built dynamically from every `AGENTSEEK_<SUFFIX>` variable
visible to pydantic-settings (`src/agentseek/env.py:91`, `:105`). The table
lists the commonly-documented suffixes; any new `AGENTSEEK_<SUFFIX>` will
alias to `BUB_<SUFFIX>` automatically.

## Settings consumed in-process

| Setting | Type | Default | Source |
| --- | --- | --- | --- |
| `AGENTSEEK_CONSOLE` | bool | `False` | `src/agentseek/env.py:48` — enables Logfire console output. |

## Docker-only variables

These are consumed by `entrypoint.sh` and `docker-compose.yml`. They have no
in-process effect outside the container.

| Variable | Default in compose | Source |
| --- | --- | --- |
| `AGENTSEEK_DOCKER_WORKSPACE` | `.` (repo root) | `docker-compose.yml:15` |
| `AGENTSEEK_WORKSPACE_PATH` | `/workspace` | `docker-compose.yml:8`, `entrypoint.sh:5` |
| `AGENTSEEK_HOME` | `/workspace/.agentseek` | `docker-compose.yml:9`, `entrypoint.sh:6` |
| `AGENTSEEK_PROJECT` | `/workspace/.agentseek/agentseek-project` | `docker-compose.yml:10`, `entrypoint.sh:9` |
| `AGENTSEEK_SKILLS_HOME` | `/workspace/.agents/skills` | `docker-compose.yml:11`, `entrypoint.sh:8` |
| `AGENTSEEK_MCP_CONFIG_PATH` | `/workspace/.agents/mcp.json` | `docker-compose.yml:12`, `entrypoint.sh:11` |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | `sqlite+pysqlite:////workspace/.agentseek/agentseek-tapes.db` | `docker-compose.yml:13` |

## `.env` loading

`AgentseekSettings` and the alias probe both load `.env` from the current
working directory with `env_ignore_empty=True` (`src/agentseek/env.py:38`,
`:26`). Empty values in `.env` are ignored. The process environment takes
precedence over `.env`.

## Precedence

For any single variable the runtime sees, top wins:

1. Explicit value in the process environment for the `BUB_*` name.
2. Explicit value in the process environment for the `AGENTSEEK_*` name (aliased into `BUB_*`).
3. `.env` value for the `BUB_*` name.
4. `.env` value for the `AGENTSEEK_*` name (aliased into `BUB_*`).
5. Default applied by `_apply_agentseek_bub_location_defaults` (for `BUB_HOME` and `BUB_PROJECT` only).

`BUB_*` always wins over `AGENTSEEK_*` for the same setting because
`apply_agentseek_env_aliases` uses `setdefault` (`src/agentseek/env.py:63`).

## See also

- How-to: `../how-to/configure-model.md`, `../how-to/configure-mcp.md`,
  `../how-to/configure-docker-workspace.md`
- Explanation: `../explanation/bub-relationship.md`
