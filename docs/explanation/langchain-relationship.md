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

AgentSeek does not replace LangChain. It gives LangChain applications a harness
for lifecycle, channels, extensions, and durable runtime data.

LangChain remains where you build graphs, agents, tools, and model calls.
AgentSeek sits around that application when you want project scaffolding,
gateway delivery, plugin-based extensions, and a database-native runtime layer.

## Why they fit together

LangChain is strong at the application layer. AgentSeek is concerned with the
operational layer around the application:

- how a project is created and run;
- how messages enter through CLI, gateway, or chat channels;
- how runtime data is captured for replay and evaluation;
- how storage, context, MCP, and framework bridges are installed.

The bridge package `agentseek-langchain` connects a LangChain runnable to the
AgentSeek runtime. Your graph remains a LangChain graph; the harness handles the
surrounding lifecycle.

## Template paths

AgentSeek includes both pure LangChain templates and harness-backed templates.
This keeps adoption gradual:

- Start with a pure LangChain template when you want the smallest dependency
  tree.
- Start with a harness-backed template when you need channels, project
  lifecycle commands, or runtime data from the beginning.
- Add AgentSeek later when a prototype needs to become an operated service.

The [templates reference](../reference/templates.md) lists the exact template
catalogue.

## When AgentSeek adds value

Use LangChain with AgentSeek when the application needs one or more of these:

- a generated project with a repeatable local run loop;
- gateway or chat-channel delivery;
- plugin-based storage, context, MCP, or observability;
- a path from local development to container build and deployment manifests;
- runtime data that can be queried and reused.

Use LangChain without AgentSeek when a small local prototype or a hosted
LangGraph runtime already covers the lifecycle you need.

## Next

- [Templates reference](../reference/templates.md)
- [Runtime data model](runtime-data-model.md)
- [Extension model](extension-model.md)
