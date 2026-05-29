---
title: What agentseek is
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - blog/introducing-agentseek.md
  - pyproject.toml
  - src/agentseek/__main__.py
---

# What agentseek is

> **In short:** agentseek is a **database-native Agent Harness**. Runtime data
> — context, tool calls, traces, tasks, feedback — lives on one durable,
> queryable substrate from the first turn. The harness ships as two PyPI
> packages split by job: `agentseek-cli` (the **project lifecycle CLI**) and
> `agentseek` (the **harness** itself, both a library you embed and a runtime
> CLI).

## Context

Most agents prove their value at runtime, then their data scatters: session context in one
place, tool calls in another, logs and eval artefacts in more pipelines. After the first
consumer, it is expensive to query, replay, compare, evaluate, or turn into training
material — see [`../blog/introducing-agentseek.md`](../blog/introducing-agentseek.md).

agentseek starts from a different assumption: context, memory, tasks, tool calls, traces,
feedback, and evaluation material should share **one durable substrate from the beginning**.
That substrate is naturally a database — hence "database-native". The harness shape exists
because most teams do not want to invent a runtime; they want to plug their app into one
that already treats runtime data as a first-class workload.

## How it works

Three pieces sit on top of each other:

1. **Bub** is the upstream runtime: a hook-first turn pipeline, channels, a
   tape store, skills, and a plugin model. agentseek consumes Bub as a regular
   library dependency (`pyproject.toml:18`). See
   <https://github.com/bubbuild/bub>.
2. **`agentseek` (the harness)** runs on top of Bub. It owns the runtime CLI
   (`chat`, `run`, `gateway`, `install`, `update`, …), the embeddable library
   surface, runtime defaults (`.agentseek/` runtime home, the
   `.agentseek/agentseek-project` install sandbox, the alias layer from
   `AGENTSEEK_*` to `BUB_*`), and the bundled skills under `src/skills/`. See
   `src/agentseek/__main__.py:52-69` for the boot sequence.
3. **`agentseek-cli` (the project lifecycle CLI)** is the second PyPI package.
   It owns scaffolding and lifecycle commands (`create / run / build / deploy
   / api / ctx / skills`). On its own it is self-contained and small; alongside
   the harness it folds in as a Bub plugin so the same `agentseek` command
   exposes the union of both surfaces. See
   [`choosing-an-entry-point.md`](choosing-an-entry-point.md).
4. **Contrib packages and your app** sit on top: storage backends, model
   routing, observability, channel adapters, and the application code that
   actually wants to run on the harness. The contrib monorepo is indexed at
   [`contrib/`](https://github.com/ob-labs/agentseek/tree/main/contrib).

In practice, most application teams depend on `agentseek` (the harness) from
their own project and let application code drive turns. The runtime CLI is a
thin Typer app over the same framework — a CLI run is a faithful preview of
what an embedded library run will produce.

## Why it is like this

- **Harness, not framework.** A harness gives you a runtime substrate and gets out of the
  way; a framework dictates how you write your agent. agentseek is intentionally the
  former, so teams that already use LangChain, DeepAgents, or their own orchestration can
  keep that and only adopt the harness underneath. The `agentseek-langchain` contrib package
  exists for exactly this case.
- **Database-native, not database-coupled.** The harness clarifies *write paths and
  semantics*; the actual store is a deployment concern. Local SQLite works out of the box;
  OceanBase / [seekdb](https://github.com/oceanbase/seekdb) is the recommended scaling path
  and ships as a contrib plugin (`agentseek-tapestore-oceanbase`).
- **Two packages, one job each.** `agentseek-cli` exists so teams that only
  need scaffolding and lifecycle commands do not have to install the harness's
  full dependency tree on their laptop or in CI; `agentseek` exists so the
  harness itself stays a regular Python package you embed in your application.
  The trade-offs and the "same name, merged surface when both are installed"
  mechanic are in [`choosing-an-entry-point.md`](choosing-an-entry-point.md).
- **Bub underneath, agentseek on top.** Rather than fork or replace Bub,
  agentseek consumes it as a regular library. The reasoning and the alias
  rules are in [`bub-relationship.md`](bub-relationship.md).

## Consequences for users

- Pick the package that matches your job. `agentseek-cli` is for project lifecycle
  work without the harness runtime on the host; `agentseek` is the harness itself
  and is what you run after `uv sync` in this repo or inside a generated project.
- Most evaluators start with Path B and `agentseek chat`
  ([`../tutorials/01-quick-demo-cli.md`](../tutorials/01-quick-demo-cli.md)).
  Most application teams start with Path A to scaffold, then Path B inside the
  generated project
  ([`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md)).
- Anywhere the documentation looks plain — environment variables, file
  layout, install sandbox semantics — that plainness is intentional. The
  complexity is concentrated in the runtime substrate (Bub + tape) and in
  optional contrib packages, not in agentseek itself.
- Tutorials, how-tos, and reference pages all assume that, once the harness
  is running, your project has a `.agentseek/` directory and that
  `AGENTSEEK_*` variables drive configuration. The why and the alias rules
  are in [`bub-relationship.md`](bub-relationship.md); the exact tables are
  in [`../reference/environment.md`](../reference/environment.md).

## Explicit non-goals

agentseek **does not** try to:

- Replace agent frameworks like LangChain, DeepAgents, LlamaIndex, or AutoGen. Use them
  alongside; route their turns through the harness via `agentseek-langchain` when needed.
- Be a generic plugin marketplace. The plugin model is Bub's; the wider catalogue lives at
  <https://hub.bub.build>. agentseek only ships and maintains the contrib packages listed
  in [`contrib/`](https://github.com/ob-labs/agentseek/tree/main/contrib).
- Ship a UI. Frontend examples live under `examples/` and use CopilotKit, AG-UI, or your
  own UI of choice.
- Hide Bub. You can always drop down to `bub …` directly when you need upstream behaviour
  unmodified — see [`bub-relationship.md`](bub-relationship.md).
- Provide a hosted service. Deployment is operator-owned; the harness gives you the
  building blocks, not a SaaS.

## Related

- Tutorial: [`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md)
- Explanation: [`bub-relationship.md`](bub-relationship.md),
  [`choosing-an-entry-point.md`](choosing-an-entry-point.md)
- Reference: [`../reference/environment.md`](../reference/environment.md),
  [`../reference/packages.md`](../reference/packages.md)
- External: [Introducing agentseek (blog)](../blog/introducing-agentseek.md),
  [Bub repository](https://github.com/bubbuild/bub),
  [Tape Systems](https://tape.systems/)
