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

A tape is the durable stream of runtime facts around a turn: the inbound
message, model calls, tool calls, tool results, anchors, and derived views.

This is the practical meaning of database-native in AgentSeek: runtime data is
not treated as throwaway logs.

Bub exposes tape persistence through the `provide_tape_store` hook. The local
default can stay lightweight during development; a project can later install a
store such as `agentseek-tapestore-oceanbase` when the same data should become
queryable SQL.

Because the tape keeps input, steps, and output in one shape, debugging,
replay, trajectory comparison, evaluation, and training can read from the same
substrate instead of separate side pipelines.

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

The important boundary is not "where can I put this file?" It is whether the
change is guidance, a declared tool, runtime behavior, or durable runtime data.

## Next

- [Extension model](extension-model.md)
- [File layout reference](../reference/file-layout.md)
- [Packages reference](../reference/packages.md)
