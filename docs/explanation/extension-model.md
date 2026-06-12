---
title: Extension model
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-06-12
sources:
  - docs/how-to/install-a-plugin.md
  - AGENTS.md
  - contrib/README.md
  - pyproject.toml
  - src/agentseek/cli/runtime.py
---

# Extension model

AgentSeek offers several extension points because not every change deserves a
plugin.

The useful question is: what kind of change are you making?

## Choose the smallest surface

Use the smallest surface that matches the change:

- **Project instructions** for durable guidance that should apply to every turn.
- **Skills** for task-specific behavior, workflows, or small helper scripts.
- **MCP servers** for external tools that can be declared in configuration.
- **Plugins** for runtime hooks, channels, stores, model providers, schedulers,
  and tool packages.
- **Contrib packages** for maintained integrations with their own dependencies,
  tests, and documentation.

This order matters. A fact should not become a Python package. A runtime hook
should not be hidden in a prompt. Keeping the surface small keeps the project
reviewable.

## How the surfaces differ

Instructions and skills shape what the agent should know or do. They are easy
to add to a workspace.

MCP entries expose tools that already live outside the Python process. They are
configuration, not application code.

Plugins change the runtime. They can add channels, tools, storage, scheduling,
or model behavior. That makes them powerful, and also worth packaging and
versioning.

Contrib packages are plugins or integrations that are large enough to own their
own README, examples, tests, and dependency set.

## Why this model exists

Agent applications evolve unevenly. One day you add a rule, the next day a
workflow, then a tool, then a storage backend.

The extension model keeps those changes in the right place so developers can
find them later and operators can tell which changes affect the runtime.

## Next

- [How to add skills](../how-to/add-skills.md)
- [How to configure MCP servers](../how-to/configure-mcp.md)
- [How to install a plugin](../how-to/install-a-plugin.md)
- [Packages reference](../reference/packages.md)
