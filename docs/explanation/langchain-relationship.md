---
title: How agentseek relates to LangChain
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-06-03
sources:
  - templates/index.json
  - contrib/agentseek-langchain/README.md
  - pyproject.toml
---

# How agentseek relates to LangChain

> **In short:** AgentSeek is **not a replacement for LangChain**, nor another
> Agent Framework. It is a database-native harness **open to any Agent
> Framework** — it ships with built-in Bub and the current version has the
> deepest integration with LangChain. It complements the LangChain open-source
> ecosystem by filling three gaps that LangSmith covers commercially but the
> open-source side currently does not: a **service-layer axis** for shipping
> graphs to production, a **semantic context layer** for memory and continual
> learning, and an **Agent-era data substrate** backed by OceanBase / seekdb.
> Your LangGraph code runs unchanged on AgentSeek — no framework switch required.

## Context

LangChain v1 and DeepAgents give developers a strong *build* foundation for
agents. But the Agent Engineering loop — build, ship, observe, refine — requires
more than a good build step. Teams that only reach "demo works locally" get
stuck there because the subsequent stages need infrastructure the open-source
ecosystem does not yet provide:

- **Ship**: a compliant Agent Protocol server that can host LangGraph / LangChain
  applications in production without rewriting them.
- **Observe + Refine**: a semantic context layer that accumulates knowledge across
  sessions and makes it retrievable — not just an ephemeral prompt injection.
- **Data substrate**: a place where runtime data (traces, tool calls, context,
  checkpoints) lives as first-class database objects from day one.

LangSmith answers all three for paying customers. AgentSeek answers them for the
open-source community.

## How it fits together

From a LangChain developer's perspective, the stack looks like this:

```text
┌────────────────────────────────────────────────────┐
│  Your LangGraph / DeepAgents application code      │  ← you write this
├────────────────────────────────────────────────────┤
│  agentseek-langchain  (bridge plugin)              │  ← zero-change integration
├────────────────────────────────────────────────────┤
│  agentseek  (harness runtime)                      │  ← gateway, channels, CLI
│  ── powered by Bub kernel under the hood           │
├────────────────────────────────────────────────────┤
│  OceanBase / seekdb / langchain-oceanbase          │  ← data substrate
└────────────────────────────────────────────────────┘
```

Key points:

- **LangChain is first-class.** The `agentseek-langchain` bridge plugin
  connects `create_agent` and `create_deep_agent` runnables directly into the
  harness. Four of the six bundled templates use LangChain — it is the primary
  supported framework.
- **Your code does not change.** You write a normal LangGraph graph; the harness
  wraps it transparently for production delivery, context management, and data
  persistence.
- **Bub is an implementation detail.** The harness runtime is built on
  [Bub](https://github.com/bubbuild/bub) (a hook-first turn pipeline with a
  plugin model). As a LangChain developer you rarely interact with Bub directly
  — it is the plumbing that makes the harness work. For those who want to
  understand the internals, see [Bub relationship](bub-relationship.md).

## What AgentSeek adds for LangChain developers

| Component | What it does | Docs |
| --- | --- | --- |
| **[agentseek-api](https://github.com/ob-labs/agentseek-api)** | Agent Protocol server (`/v1/threads`, `/v1/runs`, streaming, Store API, MCP, A2A). Your LangGraph code runs as a production service without rewriting. | [README](https://github.com/ob-labs/agentseek-api#readme) |
| **[ContextSeek](https://github.com/ob-labs/contextseek)** | Semantic context layer — unified `ContextItem`, L0/L1/L2 progressive disclosure, EvolutionEngine, DreamEngine. Fills the memory & context rot gaps that only LangSmith Context Hub covers. | [README](https://github.com/ob-labs/contextseek#readme) |
| **[langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase)** | LangGraph checkpoint + store + vectorstore + hybrid search, backed by OceanBase / seekdb / MySQL. Runtime data is queryable SQL from day one. | [README](https://github.com/oceanbase/langchain-oceanbase#readme) |
| **IM Gateway** | Feishu / DingTalk / Slack channel adapter. The agent meets users where they are, not just in a web UI. | Bundled in templates |
| **[agentseek](https://github.com/ob-labs/agentseek)** | Scaffold and manage projects (`new / dev / build / deploy`). Eliminates the scaffolding tax for each new agent project. | [Templates ref](../reference/templates.md) |
| **Development skills** | Installable guides for your coding agent (Claude Code, Cursor): `langchain-dev-guide` (pitfalls & fixes), `langchain-cn-models` (Chinese LLM integration). Your AI assistant references them while you code. | [skills/](https://github.com/ob-labs/agentseek/tree/main/skills) |

Each component has its own repository and documentation. This site covers the
**suite-level workflow** — how the components fit together. For API-level
details (endpoints, config, advanced usage), follow the links above.

## Choosing between Bub-only and LangChain templates

The templates are designed so different developer profiles land in the right
place:

| Your background | Template to start with | Runtime dependency |
| --- | --- | --- |
| New to agents, want the lightest path | `bub/default` | Bub only (no LangChain) |
| LangChain beginner, want minimal code | `langchain/markdown-messages` | LangChain + `langgraph dev` (no agentseek runtime) |
| LangChain user, need to deliver a product | `langchain/default` | LangChain + agentseek-langchain + CopilotKit + Feishu |
| Deep Research use case | `deepagents/research` | DeepAgents + Tavily (no agentseek runtime) |
| LangChain user, want harness data layer | `deepagents/default` | DeepAgents + agentseek-langchain |
| Remote graph on agentseek-api or LangSmith | `langchain/cli-remote` | LangChain + LangGraphClientRunnable |

Templates marked "no agentseek runtime" generate self-contained projects that
run with `langgraph dev` alone. They do not pull in Bub, the gateway, or the
tape store — useful when you want a pure LangChain experience and plan to adopt
the harness later. When you are ready to add the runtime data layer, switch to
a template that includes `agentseek-langchain`.

## How it works

### The bridge: `agentseek-langchain`

The `agentseek-langchain` contrib package
([contrib/agentseek-langchain/](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-langchain))
registers a Bub plugin that:

1. Wraps a LangChain `Runnable` (from `create_agent` or `create_deep_agent`)
   into a Bub turn handler.
2. Streams LangChain events (tool calls, tokens, sub-agent delegations) through
   Bub channels so the gateway and frontends receive them uniformly.
3. Persists checkpoints and store writes to the configured tape store backend
   (SQLite locally, OceanBase / seekdb in production).

From the agent author's perspective, you write a normal LangGraph graph. The
harness wraps it transparently.

### agentseek-api and Agent Protocol

`agentseek-api` ([github.com/ob-labs/agentseek-api](https://github.com/ob-labs/agentseek-api))
is a standalone FastAPI server that implements the
[Agent Protocol](https://github.com/langchain-ai/agent-protocol) — the same
HTTP spec that LangSmith Agent Server exposes externally.

You point it at a `langgraph.json` that references your graph; it handles
threads, runs, streaming, interrupt/resume, the Store API, MCP routing, and
A2A federation. No code change to your graph is required.

### ContextSeek as a LangChain Middleware peer

ContextSeek ([github.com/ob-labs/contextseek](https://github.com/ob-labs/contextseek))
is not itself a LangChain middleware — it sits as an independent semantic layer
accessible via HTTP or MCP. In practice it pairs with LangChain Middleware: a
middleware calls ContextSeek before each turn to inject relevant context, and
writes back after to persist new knowledge. The `agentseek-contextseek` contrib
package wires this up automatically inside the harness.

### Data substrate: langchain-oceanbase

`langchain-oceanbase` v0.5.0 ([github.com/oceanbase/langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase))
provides native LangGraph integrations:

- **Checkpoint saver** — durable execution state for long-running graphs.
- **Store** — cross-thread persistent memory (namespaced key-value).
- **VectorStore + Hybrid Search** — embedding-based retrieval with BM25 fusion.

All three work against OceanBase, seekdb (server or embedded), and MySQL
(checkpoint + store only). MySQL users already standardized on that stack can
adopt the agent data layer without introducing a new database — vector search
is available when they upgrade to OceanBase or seekdb. This means runtime data
is queryable SQL from day one — the same structural benefit that LangChain's
SmithDB provides internally.

## Why it is like this

- **Open to Agent Frameworks, LangChain-friendly today.** AgentSeek is designed
  to be the harness underneath any Agent Framework via its plugin model. It
  ships with built-in Bub as its native framework, and the current version has
  the deepest integration with LangChain — four of six templates, a dedicated
  bridge plugin, and native langchain-oceanbase support. We welcome new Agent
  Frameworks to connect — especially to leverage the data substrate and context
  layer. Bub is a good example: it ships built-in through exactly this pattern.
  The integration path is a contrib plugin that bridges your runnable into the
  harness.
- **Incremental adoption.** Templates like `langchain/markdown-messages` and
  `deepagents/research` carry zero agentseek runtime dependency. Developers can
  start pure-LangChain and add the harness layer later without rewriting.
- **One data layer.** Regardless of which template you start with, once you add
  the harness, runtime data flows into the same database substrate. No
  secondary data pipeline needed.

## When to use LangChain with AgentSeek vs. without

Use LangChain **with** the agentseek harness when:

- You need persistent runtime data from day one (checkpoint, store, vectorstore).
- You want IM channel delivery (Feishu, DingTalk) without writing adapters.
- You want the Agent Engineering loop (ship → observe → refine) to work out of
  the box via agentseek-api + ContextSeek.
- You want the harness CLI for project management (`new / dev / build / deploy`).

Use LangChain **without** the agentseek harness when:

- You are prototyping and want the simplest possible dependency tree.
- You deploy to LangSmith Deployments or another hosted LangGraph runtime.
- You only need `langgraph dev` locally and are not ready for production yet.

In both cases, the templates give you a working starting point in under a
minute.

## Related

- Explanation: [What agentseek is](what-agentseek-is.md),
  [How agentseek relates to Bub](bub-relationship.md),
  [Command overview](cli-surface.md)
- Reference: [Templates reference](../reference/templates.md),
  [Packages reference](../reference/packages.md)
- How-to: [How to use ContextSeek](../how-to/use-contextseek.md),
  [How to install a plugin](../how-to/install-a-plugin.md)
- External: [agentseek-api](https://github.com/ob-labs/agentseek-api),
  [ContextSeek](https://github.com/ob-labs/contextseek),
  [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase),
  [Agent Protocol](https://github.com/langchain-ai/agent-protocol)
