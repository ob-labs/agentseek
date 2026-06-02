---
title: File layout reference
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - entrypoint.sh
  - pyproject.toml
  - docs/index.md
---

# File layout reference

This page describes the **harness runtime layout**: what Path B creates once
`agentseek` is actually running. Path A by itself (`uv tool install
agentseek-cli`) does not create most of these paths until a generated project
syncs the harness in or you move into a harness environment.

agentseek touches three directories at runtime: the **runtime home** (Bub
state, config, MCP), the **workspace skills directory** (`.agents/`), and the
**plugin sandbox** (a uv project that holds installed Bub plugins).

## Local layout (no Docker)

With `BUB_HOME` / `AGENTSEEK_HOME` unset, the defaults from
`apply_agentseek_env_aliases` apply:

```text
<cwd>/
  .agentseek/                      # AGENTSEEK_HOME / BUB_HOME
    config.yml                     # Bub config (written by `agentseek onboard`)
    mcp.json                       # MCP server definitions (read by bub-mcp)
    agentseek-project/             # AGENTSEEK_PROJECT / BUB_PROJECT
      pyproject.toml               # `uv init --bare --name agentseek-project --app`
      ...                          # plugins installed by `agentseek install`
  .agents/
    skills/                        # project-local skills (Bub discovers from here)
    mcp.json                       # optional alternate MCP path
  .env                             # loaded by AgentseekSettings
```

| Path | Default source | Notes |
| --- | --- | --- |
| `.agentseek/` | `DEFAULT_AGENTSEEK_HOME` (`src/agentseek/env.py:15`) | `Path.cwd() / ".agentseek"`. |
| `.agentseek/config.yml` | `DEFAULT_AGENTSEEK_CONFIG` (`src/agentseek/env.py:18`) | Written by Bub onboarding. |
| `.agentseek/mcp.json` | `bub-mcp` default under `BUB_HOME` | Override with `AGENTSEEK_MCP_CONFIG_PATH`. |
| `.agentseek/agentseek-project/` | `DEFAULT_PLUGIN_SANDBOX` (`src/agentseek/env.py:22`) | Initialised lazily by `_ensure_plugin_sandbox` in `src/agentseek/cli.py:123`. |
| `.agents/skills/` | `entrypoint.sh:7` (container) and Bub workspace skill convention | Local runs read it directly; container symlinks it. |

## Container layout (Docker / Compose)

`docker-compose.yml` mounts `${AGENTSEEK_DOCKER_WORKSPACE:-.}` into
`/workspace` and the entrypoint pins the variables below:

```text
/workspace/                        # AGENTSEEK_WORKSPACE_PATH
  .agentseek/                      # AGENTSEEK_HOME
    mcp.json                       # link target for source mcp.json
    agentseek-project/             # AGENTSEEK_PROJECT
  .agents/
    skills/                        # AGENTSEEK_SKILLS_HOME default
    mcp.json                       # source for /workspace/.agentseek/mcp.json link
  startup.sh                       # optional, runs instead of `agentseek gateway`
```

See [Docker reference](docker.md) for the resolution order.

## Plugin sandbox semantics

`agentseek install` runs inside the directory at `AGENTSEEK_PROJECT` /
`BUB_PROJECT`. The first call uses `_ensure_plugin_sandbox`
(`src/agentseek/cli.py:123`):

1. `mkdir -p` the project path.
2. If `pyproject.toml` is already present, do nothing further.
3. Otherwise `uv init --bare --name agentseek-project --app` then
   `uv add --active --no-sync <bub-requirement>`.

The sandbox is a normal uv-managed Python project. You can inspect or edit
its `pyproject.toml` to see which plugins are installed.

The default sandbox basename must match `uv init --name`
(`src/agentseek/env.py:22` and `src/agentseek/cli.py:134`).

`agentseek install` belongs to the harness runtime CLI. A Path A environment
with only `agentseek-cli` does not create or manage this sandbox on its own.

## Bundled skills (`src/skills`)

`pyproject.toml:73` declares both `src/agentseek` and `src/skills` as build
includes. `[tool.pdm.build].skills` additionally imports selected skills
(`friendly-python`, `piglet`) from the external `PsiACE/skills` repository at
build time.

| Surface | Path in repo | Path in built wheel |
| --- | --- | --- |
| Distribution code | `src/agentseek/` | `agentseek/` |
| Bundled skills | `src/skills/` | `skills/` |
| External skills | resolved at build by `pdm-build-skills` | merged under `skills/` |

Project skills under `.agents/skills/<name>/` are **not** packaged — they
live in the user's workspace.

## See also

- How-to: [How to install a plugin](../how-to/install-a-plugin.md), [How to add skills](../how-to/add-skills.md)
- Reference: [Environment variables reference](environment.md), [Docker reference](docker.md), [Packages reference](packages.md)
