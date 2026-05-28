# Introducing agentseek

**2026-05-28**

agentseek is a **database-native Agent Harness** built on top of
[Bub](https://github.com/bubbuild/bub). It packages the upstream kernel with
opinionated workspace defaults, project-lifecycle commands, and a small set of
contrib plugins so that runtime data — context, tool calls, traces, evaluation
material — can live in a single, queryable substrate from the start.

This post explains where the project came from, what it actually is in 2026-05,
and why we keep it framed as a harness rather than a framework.

## From bubseek to agentseek

We first shipped exploratory work under the name **bubseek**. The direction —
intrinsic observability and an insight-style agent on **seekdb** — is described on
the OceanBase engineering blog:
[Intrinsic Observability: Build an Insight Agent on seekdb](https://en.oceanbase.com/blog/26947000576).

As the surface narrowed, two things became clear:

- The interesting object was not a single vertical agent. It was the **runtime
  substrate** underneath every agent run.
- A general-purpose distribution of that substrate could be useful far beyond
  insight workloads, as long as it stayed small and let teams plug in their own
  models, channels, and storage.

So we **rebranded to agentseek** and refocused the project on the harness layer —
the part of the stack that decides where data lives, how plugins are loaded, and
what a workspace looks like. The vertical pieces moved upstream into Bub, into
contrib packages, or out to separate projects.

## What agentseek is now

agentseek today is one Python distribution plus a uv workspace of contrib
packages.

The **core distribution** (`src/agentseek/`) is small:

- `apply_agentseek_env_aliases()` maps `AGENTSEEK_*` env vars onto Bub's
  `BUB_*` names (`src/agentseek/env.py:56`).
- `apply_agentseek_cli_overrides()` brands the onboarding banner, enables
  lifecycle channels in `chat`, and swaps the plugin sandbox path to
  `.agentseek/agentseek-project` (`src/agentseek/cli.py:74`).
- `__main__.py` boots a `BubFramework` and asks it for a Typer CLI
  (`src/agentseek/__main__.py:52`).

Everything else is a plugin. The bundled hard dependencies (`bub`, `bub-feishu`,
`bub-mcp`, `agentseek-schedule-sqlalchemy`, `logfire`) and the optional extras
(`ag-ui`, `cli`, `langchain`, `observability`, `oceanbase`, `context`) are listed
in [Packages reference](../reference/packages.md). The full layout — `src/`,
`contrib/`, `examples/`, `templates/`, `skills/`, `references/`, `docs/` — is
mapped in [Where things live](../explanation/where-things-live.md).

The **CLI** (`agentseek chat`, `agentseek gateway`, `agentseek install`, plus the
`agentseek-cli` lifecycle commands `create / run / build / deploy / api / ctx /
skills`) is the cheapest way to see the project working on a stranger's machine.
It is not the place to build an application around; for that, the
[harness app tutorial](../tutorials/02-first-harness-app.md) is the entry point.
The full split is in [Choosing an entry point](../explanation/choosing-an-entry-point.md).

## Why "database-native" and what it means

For a long time databases mostly held **business outcomes**: orders, users,
content, indexes, analytics tables. Agent runs lived **outside** the database:
session context in one place, tool calls and traces in another, logs and eval
artefacts in yet more pipelines. JSONL streams, Markdown notes, occasional SQLite
sidecars.

That works for one-off tasks. It is expensive once the same data needs to feed
**debugging, replay, comparison, evaluation, and training** — each consumer ends up
re-ingesting data through a new pipeline.

agentseek's bet is that the runtime artefacts belong in a **single durable layer**
from the start. Concretely, that layer is Bub's **tape**: an append-only stream of
inputs, model calls, tool calls and results, anchors, and derived views. The model
is documented at [Tape Systems](https://tape.systems/) and described as the runtime
data shape in [The runtime data model](../explanation/runtime-data-model.md).

Two consequences fall out, and we organise the project around both:

1. **Runtime data stays naturally queryable.** "Tool calls of this class over
   time", "state around this failure", "trajectories that triggered fallback"
   — all SQL (and optionally vector) queries against the tape store. No second
   indexing layer required.
2. **Context, observability, and downstream reuse share one foundation.** The
   harness clarifies the **write paths and semantics**; whether you use local
   SQLite, OceanBase, or [seekdb](https://github.com/oceanbase/seekdb) is a
   deployment and contrib concern. The OceanBase backend ships as
   `agentseek-tapestore-oceanbase` and is documented in its own
   [README](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-tapestore-oceanbase).

## Why a harness, not a framework

agentseek is deliberately **not** trying to replace your agent framework. If you
already use LangChain, DeepAgents, or your own orchestrator, route model turns
through `agentseek-langchain` and let the harness own state, channels, and the
tape. If you are starting fresh, the bundled Bub kernel is enough on its own.

The harness shape is what makes the [extension model](../explanation/extension-model.md)
small: five places to extend (project instructions, skills, plugins, MCP servers,
contrib packages) ordered by cost, with the cheapest answer usually being the right
one.

## Bub, tape, and where agentseek sits

agentseek **packages [Bub](https://github.com/bubbuild/bub)** — same hook-first
turn pipeline, channels, tape, skills, and plugin model. `agentseek` is the
distribution entry point; `.agentseek/` and `AGENTSEEK_*` are project-facing
defaults. None of Bub is forked or patched beyond the three Typer monkeypatches in
`src/agentseek/cli.py:74`. The full relationship is laid out in
[How agentseek relates to Bub](../explanation/bub-relationship.md).

The post [Why we rewrote Bub](https://bub.build/posts/why-rewrite-bub/) explains
the maintenance model: a **small, strict kernel** plus **loosely owned plugins**.
agentseek sits in that picture as the **harness and default-bundle layer** — not a
monolith that implements every store and channel itself.

## Where to start

- **Hands-on:** [Tutorials](../tutorials/index.md). The CLI demo is five minutes;
  the first harness app is the path most application developers want.
- **Look up a fact:** [Reference](../reference/index.md) for env vars, the CLI,
  packages, file layout, and Docker.
- **Decide where to put your change:** [Extension model](../explanation/extension-model.md).
- **Repository:** [ob-labs/agentseek on GitHub](https://github.com/ob-labs/agentseek).
- **Catalogue:** plugins and skills on this site's [Hub](../hub.md); the wider Bub
  ecosystem at [hub.bub.build](https://hub.bub.build).
