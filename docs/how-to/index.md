---
title: How-to index
type: how-to
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - README.md
  - docs/index.md
---

# How-to guides

Task-oriented recipes for operators and integrators. Each page assumes you
already have a working **harness** environment. If you do not, start with
[Quick demo (CLI)](../tutorials/01-quick-demo-cli.md) and
[First harness app](../tutorials/02-first-harness-app.md).

The job split from the overview matters here:

- **`agentseek` (harness)** — runtime CLI plus embeddable library, available
  after `uv sync` in this repo or in a generated project. Most pages lead with
  this path.
- **`agentseek-cli` (project lifecycle CLI)** — `create / run / build / deploy
  / api / ctx / skills`, available standalone on Path A and merged into the
  same `agentseek` command when installed alongside the harness.

Where both paths apply, a page shows the harness form first and then the
equivalent lifecycle command as a shortcut. Where only one path fits the task,
the page says so up front. Pages follow a consistent outline:
**Use this when… / Prerequisites / Numbered steps**.

## Configure

- [Configure model](configure-model.md) — pick a provider, set keys, switch models from code or
  CLI.
- [Configure MCP](configure-mcp.md) — place `mcp.json` under `.agentseek/` or `.agents/`,
  and point the harness or CLI at it.
- [Configure docker workspace](configure-docker-workspace.md) — switch workspace mount, MCP path, and
  sandbox in Compose.

## Extend

- [Install a plugin](install-a-plugin.md) — install a plugin with `agentseek install` and load
  it from the harness.
- [Add skills](add-skills.md) — register project-local skills alongside bundled ones.
- [Add an MCP server](add-mcp-server.md) — author an MCP entry that both shapes pick up.
- [Author a contrib plugin](author-a-contrib-plugin.md) — scaffold a new `contrib/agentseek-<feature>/`
  package.

## Run

- [Run locally](run-locally.md) — invoke a single turn through the harness, or with
  `agentseek run` and `agentseek chat`.
- [Run the gateway](run-gateway.md) — operate long-running channel listeners.
- [Run with Docker Compose](run-with-docker-compose.md) — Compose workflow, mounts, and env defaults.
- [Build and deploy](build-and-deploy.md) — package and ship with `agentseek build` and
  `agentseek deploy`.
- [Use ContextSeek](use-contextseek.md) — drive the `agentseek ctx` flow from the CLI, and
  consume the same context from the harness.

## Related

- Reference: [Reference](../reference/index.md)
- Concepts: [Extension model](../explanation/extension-model.md)
