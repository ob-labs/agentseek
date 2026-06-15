---
title: LangChain relationship
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-06-12
sources:
  - templates/index.json
  - contrib/agentseek-langchain/README.md
  - pyproject.toml
---

# LangChain relationship

AgentSeek does not replace LangChain. It is a database-native harness open to
agent frameworks, with the deepest integration aimed at LangChain and
DeepAgents today.

LangChain remains where you build graphs, agents, tools, and model calls.
AgentSeek surrounds that application with the pieces that usually appear after
the prototype works: service delivery, semantic context, runtime extensions,
and durable runtime data.

## Why they fit together

LangChain is strong at the build layer. AgentSeek is concerned with the agent
engineering loop around it:

- **Ship**: gateway, channels, project commands, and production service paths.
- **Observe and refine**: runtime data that can be replayed, inspected, and
  evaluated.
- **Remember**: ContextSeek and related extensions for semantic context across
  turns and sessions.
- **Store**: OceanBase, seekdb, or another supported backend for agent-era
  data such as checkpoints, tool calls, traces, memory, and feedback.

The bridge package `agentseek-langchain` connects a LangChain runnable to the
AgentSeek runtime. Your graph remains a LangChain graph; the harness handles the
surrounding lifecycle.

```text
LangGraph or DeepAgents application
  -> agentseek-langchain bridge
  -> AgentSeek harness on the Bub runtime
  -> tape store, ContextSeek, gateway, channels, and plugins
```

## What AgentSeek adds

| Layer | What it adds |
| --- | --- |
| Service layer | `agentseek-api`, gateway delivery, generated frontend/runtime projects, and deployment artifacts. |
| Semantic context | ContextSeek integration through HTTP, MCP, or contrib packages. |
| Data substrate | Tape stores, checkpoints, memory, vector or hybrid search, and OceanBase / seekdb integrations. |
| Extension surface | Bub-compatible plugins for channels, model providers, MCP, stores, schedulers, and observability. |

The important part is that these layers are additive. A LangChain graph does
not need to become a Bub application to benefit from the harness.

## Template paths

AgentSeek includes both pure LangChain templates and harness-backed templates.
This keeps adoption gradual:

- Start with a pure LangChain template when you want the smallest dependency
  tree or plan to run with `langgraph dev`.
- Start with a harness-backed template when you need channels, project
  lifecycle commands, or runtime data from the beginning.
- Add AgentSeek later when a prototype needs service delivery, memory,
  evaluation, or a database-backed runtime layer.

The [templates reference](../reference/templates.md) lists the exact template
catalogue.

## When AgentSeek adds value

Use LangChain with AgentSeek when the application needs one or more of these:

- a generated project with a repeatable local run loop;
- gateway or chat-channel delivery;
- plugin-based storage, context, MCP, scheduling, or observability;
- a path from local development to container build and deployment manifests;
- runtime data that can be queried and reused.

Use LangChain without AgentSeek when a small local prototype or a hosted
LangGraph runtime already covers the lifecycle you need.

## Next

- [Templates reference](../reference/templates.md)
- [Runtime data model](runtime-data-model.md)
- [Extension model](extension-model.md)
