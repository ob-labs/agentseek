---
title: What agentseek is
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-06-08
sources:
  - README.md
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/surface.py
---

# What agentseek is

AgentSeek is a database-native agent harness with one CLI entry point and an
embeddable Python runtime. It helps teams build, run, and operate agent
applications whose runtime data is durable, queryable, and ready for replay or
evaluation.

The public command surface is:

- `agentseek create/run/build/deploy` for project management.
- `agentseek chat/turn/gateway` for runtime execution.
- `agentseek plugin/ctx/skills/api` for extensions and service bridges.

## Context

Agent data tends to scatter after the first demo: session context, tool calls,
logs, eval artifacts, feedback, and traces land in different systems. AgentSeek
starts from the opposite assumption: those runtime facts should share one
durable substrate from the beginning.

That substrate is naturally a database. The harness exists so teams can keep
their preferred agent framework while adopting a runtime layer that treats data
as a first-class workload.

## How it works

1. **Bub** supplies the hook-first runtime kernel: channels, turns, tapes,
   skills, plugins, and base CLI behavior.
2. **AgentSeek** layers product defaults on top: `.agentseek/` runtime home,
   environment aliases, onboarding branding, the plugin sandbox, command layout,
   project commands, and bundled skills.
3. **Contrib packages and applications** add storage backends, LangChain
   bridges, UI adapters, context systems, schedules, and the actual application
   code.

## Design choices

- **Harness, not framework.** AgentSeek does not dictate how agents are written.
  LangChain, DeepAgents, Bub-native apps, and custom orchestrators can run on
  top of it.
- **Database-native, not database-coupled.** Local SQLite is useful for
  development; OceanBase-backed storage can be introduced through contrib
  packages when scale or compatibility matters.
- **One entry point.** Project management and runtime commands share `agentseek`
  so users do not have to remember which package or binary owns a task.
- **Bub underneath.** AgentSeek composes Bub instead of hiding it. You can still
  drop to Bub when you need upstream behavior.

## Non-goals

AgentSeek does not try to replace agent frameworks, become a generic plugin
marketplace, ship a hosted SaaS, or force a specific UI. It provides the harness
and the runtime substrate; application and deployment choices remain explicit.

## Related

- [Command overview](cli-surface.md)
- [How AgentSeek relates to Bub](bub-relationship.md)
- [How AgentSeek relates to LangChain](langchain-relationship.md)
- [Runtime data model](runtime-data-model.md)
