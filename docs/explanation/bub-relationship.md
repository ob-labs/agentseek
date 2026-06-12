---
title: Bub relationship
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-06-12
sources:
  - src/agentseek/env.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/__main__.py
  - pyproject.toml
  - entrypoint.sh
---

# Bub relationship

AgentSeek is a distribution built on Bub. It is not a fork.

Bub supplies the runtime kernel: turns, channels, hooks, tape, skills, plugins,
and the base CLI application. AgentSeek adds the project defaults, command
layout, templates, and naming that make the kernel feel like a complete
workspace tool.

## Why Bub is underneath

Bub keeps the runtime small and extension-oriented. That is useful for
AgentSeek because most production choices are project-specific: storage,
channels, model providers, MCP tools, schedules, and framework bridges.

AgentSeek can therefore stay focused on the project lifecycle while Bub remains
the common runtime vocabulary.

## What AgentSeek changes

AgentSeek changes the distribution surface, not the runtime model:

- `AGENTSEEK_*` variables fill matching `BUB_*` variables when the `BUB_*` value
  is not already set.
- `.agentseek/` becomes the default runtime home.
- `.agentseek/agentseek-project/` becomes the default plugin sandbox.
- Bub commands are grouped under the `agentseek` lifecycle-oriented CLI.
- Project commands such as `create`, `run`, `build`, and `deploy` are added.

## What stays Bub

The turn pipeline, channel system, hook model, plugin entry points, tape
semantics, and skill discovery remain Bub concepts. A plugin author can target
Bub entry points and still work under AgentSeek.

## When to use each CLI

Use `agentseek` for project work: templates, workspace defaults, plugin
installation, generated apps, gateway operation, and the lifecycle commands.

Use `bub` directly when you need to reproduce upstream Bub behavior without
AgentSeek defaults, or when you are developing a Bub plugin and want to verify
that it does not depend on AgentSeek.

## Next

- [CLI reference](../reference/cli.md)
- [Runtime data model](runtime-data-model.md)
- [Environment variables reference](../reference/environment.md)
