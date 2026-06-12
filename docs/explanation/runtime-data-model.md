---
title: Runtime data model
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-06-12
sources:
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
  - pyproject.toml
  - contrib/README.md
---

# Runtime data model

AgentSeek uses a small runtime vocabulary: turns, channels, tapes, skills, MCP,
and plugins.

These concepts explain what enters the harness, what changes behavior, and
where durable data lands.

```text
user or app
  -> channel
  -> turn
  -> runtime hooks from plugins
  -> model, tools, skills, MCP
  -> tape
```

## Turn

A turn is one interaction with the runtime. It has an inbound message, runtime
context, model activity, optional tool calls, and an outbound response.

## Channel

A channel is the surface where a turn enters and leaves. CLI chat, gateway,
Feishu, Telegram, and AG-UI are channel examples.

Channels let the same application meet users in different places without
rewriting the agent.

## Tape

A tape is the durable record of runtime facts. It captures the interaction and
the steps around it so the data can be replayed, inspected, compared, or used
for evaluation.

This is the practical meaning of database-native in AgentSeek: runtime data is
not treated as throwaway logs.

## Skill

A skill is task knowledge packaged as Markdown and optional helper files. It
guides the agent, but it does not add runtime hooks or new channels.

Use a skill when the change is about how the agent should approach a task.

## MCP

MCP declares external tools that the model can call. It is useful when a tool
already exists outside the Python process and can be exposed through a server
configuration.

## Plugin

A plugin changes runtime behavior. Plugins add hooks, channels, storage,
schedulers, model providers, and tool packages.

Use a plugin when the runtime itself needs a new capability.

## Why the separation matters

Each concept has a different maintenance cost. Skills are cheap. MCP entries
are configuration. Plugins affect the runtime. Tapes are the durable substrate.

Keeping those roles separate makes the project easier to operate and easier to
extend.

## Next

- [Extension model](extension-model.md)
- [File layout reference](../reference/file-layout.md)
- [Packages reference](../reference/packages.md)
