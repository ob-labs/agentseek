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

> **In short:** the `agentseek` **harness package** is a distribution of Bub, not a fork. It
> boots the same framework, adds project-local defaults under `.agentseek/`, brands the CLI,
> and lets `AGENTSEEK_*` environment variables act as fallbacks for the matching `BUB_*`
> variables. When you need upstream behaviour unmodified, the `bub` CLI and Python API are
> right there.

## Context

[Bub](https://github.com/bubbuild/bub) is the runtime kernel: a hook-first turn pipeline,
channels, tape, skills, and a plugin model exposed through the `[project.entry-points.bub]`
group. The kernel is intentionally small; everything interesting is a plugin.

The `agentseek` harness package wraps that kernel for "a real project running in a real
workspace". That means opinionated defaults (where data lives, what variables look like,
what the install sandbox is named, what skills come bundled) and a brand for the CLI. It
does not mean replacing, extending, or hiding Bub: `agentseek` depends on Bub as a regular distribution
(`pyproject.toml:19`, `bub>=0.3.7`) and the CLI is created by
`BubFramework.create_cli_app()` after agentseek-specific overrides are applied
(`src/agentseek/__main__.py:52-69`).

## How it works

### Boot order

When you run `agentseek …`, the entry point does three things, in order
(`src/agentseek/__main__.py:18-19`):

1. `apply_agentseek_env_aliases()` — copy `AGENTSEEK_*` values into the matching `BUB_*`
   names so the rest of the stack reads its config from one prefix.
2. `apply_agentseek_runtime_overrides()` — rebrand the onboard banner, swap the chat command so
   Bub support channels are enabled, adjust plugin-install defaults, and route AgentSeek package
   requirements directly.
3. `create_cli_app()` instantiates `BubFramework(config_file=agentseek_config_file())` and
   asks it for a Typer app. From that point on the runtime is plain Bub.

The same is true of the Docker entrypoint (`entrypoint.sh:5-45`): it resolves
`BUB_*`/`AGENTSEEK_*` pairs and exports both, then execs
`${workspace_path}/startup.sh` if it exists, otherwise falls back to
`agentseek gateway`.

### Alias mapping

The alias rule lives in
`src/agentseek/env.py:56-65` (`apply_agentseek_env_aliases`) and
`src/agentseek/env.py:105-114` (`_bub_aliases`):

- For every variable in the process environment or the local `.env` file whose name starts
  with `AGENTSEEK_` and whose value is non-empty, agentseek **sets** `BUB_<suffix>` to the
  same value **iff `BUB_<suffix>` is not already set** (`setdefault` semantics, line 64).
- A pre-existing `BUB_*` variable therefore wins over the `AGENTSEEK_*` alias. This is the
  "BUB takes precedence" rule that the contrib README also calls out
  ([contrib/](https://github.com/ob-labs/agentseek/tree/main/contrib)).

In addition, two location defaults are applied unconditionally when missing
(`src/agentseek/env.py:68-73`):

| Variable | Default when unset | Source |
| --- | --- | --- |
| `BUB_HOME` | `${cwd}/.agentseek` | `src/agentseek/env.py:15` (`DEFAULT_AGENTSEEK_HOME`) and `src/agentseek/env.py:86-88` |
| `BUB_PROJECT` | `${BUB_HOME}/agentseek-project` | `src/agentseek/env.py:22` (`DEFAULT_PLUGIN_SANDBOX`) and `src/agentseek/env.py:70-73` |

The full per-variable table — including model, API key, MCP path, skills home, workspace —
lives in [Environment variables reference](../reference/environment.md).

### CLI overrides

The CLI starts from Bub's app, then AgentSeek applies a small command-layout layer:

- The onboarding banner reads `AGENTSEEK` instead of `BUB`
  (`src/agentseek/cli/runtime.py:23-32`, `74-80`). No workflow change.
- `chat` is replaced so Bub support channels (`*.lifecycle`) are enabled alongside `cli`
  (`src/agentseek/cli/runtime.py:83-112`). This is what lets MCP and similar helpers boot inside a
  CLI chat session.
- `plugin install` resolves a fresh plugin sandbox under `.agentseek/agentseek-project` instead of
  Bub's `bub-project`, by replacing `_ensure_project` with `_ensure_plugin_sandbox`
  (`src/agentseek/cli/runtime.py:115-140`). The directory is `uv init --bare --name agentseek-project`-ed
  on demand if it does not exist.
- Bub's root `run` command is exposed as `agentseek turn`.
- Bub's root plugin mutation commands are grouped under `agentseek plugin`.

AgentSeek-owned project commands are mounted by `src/agentseek/cli/surface.py`; runtime behavior still
flows through Bub.

## Why it is like this

- **Defaults belong to the distribution, not the kernel.** Bub stays generic; agentseek
  owns the "what a project workspace looks like" decisions. Other distributions could make
  different choices without touching Bub.
- **Aliases are one-way and BUB wins.** Plugin authors can target the upstream prefix and
  still work cleanly under agentseek, because the alias only fills in gaps. This is why the
  contrib README tells plugin authors to prefer `AGENTSEEK_*` only for distribution-scoped
  settings and let `BUB_*` own runtime behaviour ([contrib/](https://github.com/ob-labs/agentseek/tree/main/contrib)).
- **No private fork of Bub.** Bub is a normal dependency, pinned by version in
  `pyproject.toml:19`. Upgrading Bub upgrades agentseek; nothing in agentseek vendors or
  patches the kernel beyond the three Typer monkeypatches above.

## Consequences for users

- You can compare `uv run bub --help` and `uv run agentseek --help` when debugging, but the
  command surfaces are intentionally not identical. AgentSeek adds project command groups and
  normalizes ambiguous root commands.
- Whatever you put in `AGENTSEEK_*` will leak into `BUB_*` for the duration of the process,
  unless `BUB_*` was already set. This matters when you debug a plugin that only documents
  the `BUB_*` name.
- The defaults the alias layer applies (`.agentseek` home, `agentseek-project` sandbox)
  show up the first time you run any `agentseek` command in a workspace. Operators who
  prefer system-wide layouts should set `BUB_HOME` and `BUB_PROJECT` explicitly.
- If a problem reproduces under `agentseek` but not under `bub`, the suspect is one of the
  overrides in `src/agentseek/cli/runtime.py` or the alias step in
  `src/agentseek/env.py:56`. Bisect by running the same command with `bub` directly.

## When to use `bub` directly

Reach for the upstream CLI when:

- You want to **reproduce a Bub Hub** (<https://hub.bub.build>) example exactly as documented.
- You are **developing a Bub plugin** and want to make sure it does not silently depend on
  agentseek defaults — run it under `bub` with the upstream sandbox and Bub-prefixed env.
- You want **no project-local `.agentseek/` directory** in the workspace and prefer to
  manage `BUB_HOME` yourself, for example in a multi-tenant container.
- You are diagnosing whether a bug lives in Bub or in the agentseek overrides.

Reach for `agentseek` when you want the opinionated defaults: a workspace-local home, the
AgentSeek plugin install sandbox, Bub support channels in chat mode, project command groups,
and the `AGENTSEEK_*` naming.

## Related

- Tutorial: [02 — Build your first harness app](../tutorials/02-first-harness-app.md)
- How-to: [How to install a plugin](../how-to/install-a-plugin.md),
  [How to configure the model provider](../how-to/configure-model.md)
- Reference: [Environment variables reference](../reference/environment.md),
  [CLI reference](../reference/cli.md)
- Explanation: [The runtime data model](runtime-data-model.md)
- External: [Bub repository](https://github.com/bubbuild/bub),
  [Bub Hub](https://hub.bub.build),
  [Why we rewrote Bub](https://bub.build/posts/why-rewrite-bub/)
