---
title: What AgentSeek is
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-06-12
sources:
  - README.md
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
---

# What AgentSeek is

AgentSeek is a database-native harness for agent applications.

It gives a project one operational surface for the whole lifecycle: create a
starter project, run it locally, attach runtime extensions, build an image, and
operate channels such as CLI, gateway, or chat integrations.

## The problem it solves

Agent projects usually start with code and prompts. The runtime facts arrive
later: messages, tool calls, context, traces, checkpoints, feedback, and
evaluation data.

If those facts land in unrelated systems, replay and operation become hard.
AgentSeek starts from the opposite model: runtime data should be durable and
queryable from the beginning.

## The model

AgentSeek separates three concerns:

- **Application code** stays in the project you generate or embed.
- **Runtime behavior** flows through Bub: turns, channels, hooks, plugins, and
  skills.
- **Runtime data** lands in a durable store through the tape model.

That makes AgentSeek a harness, not a replacement for agent frameworks. A
LangChain, DeepAgents, Bub-native, or custom app can run through the same
lifecycle without giving up its own application structure.

## What AgentSeek owns

AgentSeek owns the distribution-level choices that make the harness usable in a
project:

- one `agentseek` command;
- workspace-local runtime defaults under `.agentseek/`;
- project templates;
- plugin and skill entry points;
- Docker and gateway entry points;
- `AGENTSEEK_*` environment aliases for the Bub runtime.

## What it does not own

AgentSeek does not require a specific agent framework, database backend,
frontend, or hosted service. Those choices belong to your application and the
extensions you install.

## Next

- [Runtime data model](runtime-data-model.md)
- [Extension model](extension-model.md)
- [Bub relationship](bub-relationship.md)
- [LangChain relationship](langchain-relationship.md)
