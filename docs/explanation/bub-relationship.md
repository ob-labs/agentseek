---
title: How agentseek relates to Bub
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/__main__.py
  - pyproject.toml
  - entrypoint.sh
---

# How agentseek relates to Bub

> **In short:** `agentseek` is a distribution of Bub, not a fork. It boots the same
> framework, adds project-local defaults under `.agentseek/`, brands the CLI, and lets
> `AGENTSEEK_*` environment variables act as fallbacks for the matching `BUB_*` variables.
> When you need upstream behaviour unmodified, the `bub` CLI is right there.

## Context

[Bub](https://github.com/bubbuild/bub) is the runtime kernel: a hook-first turn pipeline,
channels, tape, skills, and a plugin model. The kernel is intentionally small; everything
interesting is a plugin.

`agentseek` wraps that kernel for "a real project running in a real workspace". That means
opinionated defaults (where data lives, what variables look like, what the install sandbox is
named) and a branded CLI. It does not mean replacing or hiding Bub: `agentseek` depends on
Bub as a regular distribution (`bub>=0.3.7`) and the runtime is plain Bub once started.

## How it works

### Boot order

When you run `agentseek …`, the entry point:

1. Maps `AGENTSEEK_*` env vars onto the matching `BUB_*` names so the rest of the stack
   reads its config from one prefix.
2. Boots a `BubFramework`, asks it for a CLI app, then replaces Bub's builtin commands
   with AgentSeek's own branded implementations.

The Docker entrypoint does the same: it resolves `BUB_*`/`AGENTSEEK_*` pairs, exports both,
then execs `${workspace_path}/startup.sh` if it exists, otherwise falls back to
`agentseek gateway`.

### Environment alias mapping

- For every variable whose name starts with `AGENTSEEK_` and whose value is non-empty,
  agentseek **sets** `BUB_<suffix>` to the same value **only if `BUB_<suffix>` is not
  already set** (setdefault semantics).
- A pre-existing `BUB_*` variable therefore wins over the `AGENTSEEK_*` alias.

In addition, two location defaults are applied when missing:

| Variable | Default when unset |
| --- | --- |
| `BUB_HOME` | `${cwd}/.agentseek` |
| `BUB_PROJECT` | `${BUB_HOME}/agentseek-project` |

The full per-variable table — including model, API key, MCP path, skills home, workspace —
lives in [Environment variables reference](../reference/environment.md).

### CLI command layout

AgentSeek's CLI starts from Bub's app but presents a different command surface:

- **`onboard`** — same config-collection workflow, branded with the AgentSeek banner.
- **`chat`** — enables Bub support channels (`*.lifecycle`) alongside `cli`, so MCP and
  similar helpers can boot inside a CLI chat session.
- **`plugin install / uninstall / update`** — grouped under `agentseek plugin`. Uses the
  `.agentseek/agentseek-project` sandbox and routes `agentseek-*` packages directly to PyPI.
- **`turn`** — Bub's single-message `run` command, exposed under a non-ambiguous name.
- **`create / run / build / deploy`** — project lifecycle commands owned by AgentSeek.
- **`api / ctx / skills`** — service forwarding commands owned by AgentSeek.

Runtime behavior (turn pipeline, channels, hooks, tape) still flows through Bub unchanged.

## Why it is like this

- **Defaults belong to the distribution, not the kernel.** Bub stays generic; agentseek
  owns the "what a project workspace looks like" decisions. Other distributions could make
  different choices without touching Bub.
- **Aliases are one-way and BUB wins.** Plugin authors can target the upstream prefix and
  still work cleanly under agentseek, because the alias only fills in gaps.
- **No private fork of Bub.** Bub is a normal dependency pinned by version. Upgrading Bub
  upgrades agentseek; nothing in agentseek vendors or patches the kernel.

## What this means in practice

- `uv run bub --help` and `uv run agentseek --help` show different command surfaces.
  AgentSeek adds project commands and reorganizes runtime commands into panels.
- Whatever you put in `AGENTSEEK_*` will propagate to `BUB_*` for the duration of the
  process, unless `BUB_*` was already set.
- The defaults (`.agentseek` home, `agentseek-project` sandbox) appear the first time you
  run any `agentseek` command in a workspace. Operators who prefer system-wide layouts
  should set `BUB_HOME` and `BUB_PROJECT` explicitly.
- If a problem reproduces under `agentseek` but not under `bub`, bisect by running the same
  command with `bub` directly.

## When to use `bub` directly

Reach for the upstream CLI when:

- You want to reproduce a [Bub Hub](https://hub.bub.build) example exactly as documented.
- You are developing a Bub plugin and want to make sure it does not silently depend on
  agentseek defaults.
- You want no project-local `.agentseek/` directory and prefer to manage `BUB_HOME` yourself.
- You are diagnosing whether a bug lives in Bub or in the agentseek layer.

Reach for `agentseek` when you want the opinionated defaults: a workspace-local home, the
AgentSeek plugin sandbox, support channels in chat mode, project commands, and the
`AGENTSEEK_*` naming.

## Related

- Tutorial: [02 — Build your first harness app](../tutorials/02-first-harness-app.md)
- How-to: [How to install a plugin](../how-to/install-a-plugin.md),
  [How to configure the model provider](../how-to/configure-model.md)
- Reference: [Environment variables reference](../reference/environment.md),
  [CLI reference](../reference/cli.md)
- Explanation: [The runtime data model](runtime-data-model.md)
- External: [Bub repository](https://github.com/bubbuild/bub),
  [Bub Hub](https://hub.bub.build)
