---
title: How-to index
type: how-to
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
---

# How-to guides

Task-oriented recipes. Each page assumes you already have a working agentseek
install. If you do not, start with `../tutorials/01-quick-demo-cli.md` and
`../tutorials/02-first-harness-app.md`.

How-to pages prefer the **library / config-file form first**, then add a small
`### CLI shortcut` block where applicable. The CLI is the demo entry, not the
recommended product surface (see `../explanation/choosing-an-entry-point.md`).

## Configure

- `configure-model.md` — pick a provider, set keys, switch models.
- `configure-mcp.md` — place `mcp.json` under `.agentseek/` or `.agents/`.
- `configure-docker-workspace.md` — switch workspace mount, MCP path, sandbox in
  Compose.

## Extend

- `install-a-plugin.md` — `agentseek install` and the plugin sandbox.
- `add-skills.md` — project-local vs bundled skills.
- `add-mcp-server.md` — author an MCP entry.
- `author-a-contrib-plugin.md` — new `contrib/agentseek-<feature>/` package.

## Run

- `run-locally.md` — `agentseek run` and `agentseek chat`.
- `run-gateway.md` — long-running channel listeners.
- `run-with-docker-compose.md` — Compose workflow, mounts, env defaults.
- `build-and-deploy.md` — `agentseek build` and `agentseek deploy`.
- `use-contextseek.md` — `agentseek ctx` flow.

## Related

- Reference: `../reference/index.md`
- Concepts: `../explanation/extension-model.md`
