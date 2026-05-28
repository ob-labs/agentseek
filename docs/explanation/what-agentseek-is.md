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

> **In short:** agentseek is a **database-native Agent Harness** distributed as a Python
> library you embed in your own application. It packages [Bub](https://github.com/bubbuild/bub)
> with project-local defaults so runtime data — context, tool calls, traces, tasks, feedback —
> lives on one durable substrate from the first turn. The CLI is a demo entry point, not the
> product.

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

1. **Bub** provides the kernel: a hook-first turn pipeline, channels, a tape store, skills,
   and a plugin model. See <https://github.com/bubbuild/bub>.
2. **agentseek** packages Bub with project-local defaults (`.agentseek/` runtime home,
   `AGENTSEEK_*` environment aliases, an install sandbox at `.agentseek/agentseek-project`,
   bundled skills under `src/skills/`) — see `src/agentseek/__main__.py:18` for the boot
   sequence and `pyproject.toml:18` for the dependency on Bub.
3. **Contrib packages and your app** sit on top: storage backends, model routing,
   observability, channel adapters, and the application code that actually wants to run on
   the harness. The contrib monorepo is indexed at [`contrib/`](https://github.com/ob-labs/agentseek/tree/main/contrib).

In practice the recommended path is to depend on `agentseek` from your project (`pyproject.toml`
declares it as a regular distribution under `[project] name = "agentseek"`,
`pyproject.toml:2`) and let your application code drive turns. The CLI happens to be a thin
Typer app that boots the exact same framework — see `src/agentseek/__main__.py:52-69` — which
is why the CLI demo is a faithful preview of what your app will get.

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
- **CLI as demo, not product.** Putting the CLI front-and-centre would mis-signal what the
  project is. The CLI is real and supported, but it is the on-ramp for evaluators, not the
  surface app developers build against. See
  [`choosing-an-entry-point.md`](choosing-an-entry-point.md).
- **Bub underneath, agentseek on top.** Rather than fork or replace Bub, agentseek wraps it
  and supplies opinionated defaults. The reasoning is in
  [`bub-relationship.md`](bub-relationship.md).

## Consequences for users

- You are expected to **embed agentseek in an application**. Library use is the main path;
  see [`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md).
- Anywhere the documentation looks plain — environment variables, file layout, install
  sandbox semantics — that plainness is intentional. The complexity is concentrated in the
  runtime substrate (Bub + tape) and in optional contrib packages, not in agentseek itself.
- Tutorials, how-tos, and reference pages all assume that your project has a `.agentseek/`
  directory and that `AGENTSEEK_*` variables drive configuration. The why and the alias
  rules are in [`bub-relationship.md`](bub-relationship.md); the exact tables are in
  [`../reference/environment.md`](../reference/environment.md).

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
