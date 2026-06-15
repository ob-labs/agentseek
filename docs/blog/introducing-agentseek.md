---
title: Introducing AgentSeek
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-06-15
sources:
  - README.md
  - docs/explanation/what-agentseek-is.md
  - docs/explanation/runtime-data-model.md
  - docs/explanation/bub-relationship.md
  - docs/explanation/langchain-relationship.md
---

# Introducing AgentSeek

**2026-06-15**

AgentSeek is a database-native harness for agent applications. It helps teams
turn runtime data into a database workload: turns, context, tool calls, tasks,
feedback, checkpoints, memory, and observability data stay queryable instead of
being scattered across logs and side systems.

That framing is the project. AgentSeek is not another agent framework. It is
the layer around a framework that decides how a project is created, how a turn
enters through a channel, which extensions run, and where the runtime facts
land.

## From bubseek to AgentSeek

The earliest work explored an insight-style agent on seekdb under the name
`bubseek`. The useful part turned out to be more general than one vertical
agent: every serious agent project needs a durable runtime substrate.

AgentSeek keeps that substrate small. Bub supplies the runtime kernel: turns,
channels, hooks, tape, skills, and plugins. AgentSeek packages it with project
defaults, templates, contrib integrations, and a public `agentseek` command.

## Why database-native

Agent runs create useful facts before they create stable products. Messages,
tool calls, traces, checkpoints, feedback, and memory all become valuable later
for debugging, replay, evaluation, and training.

If each consumer gets its own log or side pipeline, the project becomes harder
to operate. AgentSeek instead treats the tape as the durable stream of runtime
facts. A local project can start small, then move the same shape of data into
OceanBase, seekdb, or another supported store when it needs a stronger backend.

Database-native does not mean database-coupled. The harness defines the runtime
shape and extension points; the storage backend remains a deployment choice.

## Why a harness

Frameworks such as LangChain and DeepAgents are where developers build graphs,
agents, tools, and model calls. AgentSeek sits around that application when it
needs service delivery, semantic context, runtime extensions, and queryable
runtime data.

That is why the recommended template is `deepagents/default`: it gives a
DeepAgents runnable inside the AgentSeek harness, while still keeping the app
code recognizable.

## Where to start

- Build the recommended app from `deepagents/default`: [Templates reference](../reference/templates.md).
- Understand the data model: [Runtime data model](../explanation/runtime-data-model.md).
- See how LangChain and DeepAgents fit: [LangChain relationship](../explanation/langchain-relationship.md).
- Browse integrations: [Hub](../hub.md).
