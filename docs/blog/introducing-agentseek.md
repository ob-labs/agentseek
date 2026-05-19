# Introducing agentseek

**2026-05-18**

## From bubseek to agentseek

We first shipped exploratory work under the name **bubseek**. The direction—**intrinsic observability** and an insight-style agent on **seekdb**—is described on the OceanBase engineering blog: [Intrinsic Observability: Build an Insight Agent on seekdb](https://en.oceanbase.com/blog/26947000576). As we narrowed the product to a **database-native Agent Harness**—rather than carrying every vertical-specific detail of a single distribution—we **rebranded to agentseek** and continued development in this repository and docs.

That article frames **why agent trails belong in the database** and how seekdb can host them; agentseek keeps the same bet—**runtime data is valuable on its own**—while tightening the **product boundary** to **harness and distribution defaults**. Deeper domain products and data stacks stay upstream or in **contrib**.

## The problem we are solving

For a long time databases mostly held **business outcomes**: orders, users, content, indexes, analytics tables. Agent runs often lived **outside** the database: session context in one place, tool calls and traces in another, logs and eval artefacts in yet more pipelines. Common patterns include JSONL-style local streams, Markdown notes, and occasional SQLite sidecars.

That works well for one-off tasks, but it makes **post-hoc debugging, replay, comparison, evaluation, and training** expensive: after the first consumer, data is hard to reuse without copying it through more systems. Teams then stack observability and dataset tooling (for example LangSmith or Phoenix), which adds deployment and ops surface.

As agents move from personal demos to **always-on team infrastructure**, the trend sharpens: “memory” is less about static profiles and more about **trace-shaped, multi-layer indexes**; the durable value is often not only the final answer but **how context was assembled, how work progressed, how tools were invoked, how state changed, and how errors and feedback were recorded**. Whoever can host that substrate directly is better positioned as foundational infrastructure.

## Why a database-native harness

agentseek is **not** trying to replace every agent framework. It is a **database-native Agent Harness** (plus opinionated defaults and extension surfaces) so that **context, memory, task state, tool calls, traces, feedback, and eval material** land in a **single queryable, reusable** durable layer from the start—and can feed later consumption without a separate re-ingestion project.

The [ob-labs/agentseek](https://github.com/ob-labs/agentseek) README states the assumption plainly: keep those runtime artefacts on one durable substrate so the same data can serve debugging, replay, trajectory comparison, evaluation, analysis, and training.

From a database-shaped lens, two consequences follow (and we align engineering with both):

1. **Runtime data stays naturally queryable**—for example “tool calls of this class over time” or “state around this failure”—without bolting on yet another indexing layer when the store already speaks SQL (and optionally vectors).
2. **Context, observability, and downstream reuse share one foundation**—instead of a default split where “sessions live in A, metrics in B, training exports in C.” The harness clarifies **write paths and semantics**; whether you use local SQLite, OceanBase, or [seekdb](https://github.com/oceanbase/seekdb) is a deployment and **contrib** concern.

## Bub, tape, and where agentseek sits

agentseek **packages [Bub](https://github.com/bubbuild/bub)**: the same **hook-first** turn pipeline, channels, **tape**, skills, and plugin model, with `agentseek` as the distribution entry point and `.agentseek` / `AGENTSEEK_*` as project-facing defaults.

[Tape Systems](https://tape.systems/) describes tape as a unified fact model: append-only entries, anchors, and derived views so long-running work, observability, evaluation, and training can sit on **one append-only fact stream** instead of shadow logs per outlet. Bub treats tape seriously in the kernel and exposes persistence through hooks such as `provide_tape_store`; that is the same axis as “runtime data belongs in the database.”

The post [Why we rewrote Bub](https://bub.build/posts/why-rewrite-bub/) explains the maintenance model: a **small, strict kernel** plus **loosely owned plugins**. agentseek sits in that picture as the **harness and default bundle** layer—not a monolith that implements every store and channel itself.

## Where to start

- **Hands-on:** [Getting started](../docs/getting-started.md).
- **Repository:** [ob-labs/agentseek on GitHub](https://github.com/ob-labs/agentseek).
- **Catalogue:** plugins and skills on this site’s [Hub](../hub.md); the wider Bub ecosystem at [hub.bub.build](https://hub.bub.build).
