---
title: Lifecycle Toolkit
type: explanation
audience: [A2, A5]
runs: no
verified_on: 2026-07-07
sources:
  - README.md
  - docs/get-started/index.md
  - docs/guides/create-project.md
  - docs/guides/inspect-project.md
  - docs/guides/check-project.md
  - docs/guides/run-local-development.md
  - docs/guides/run-project-tasks.md
  - docs/reference/lifecycle-spec.md
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/lifecycle/core.py
---

# Lifecycle Toolkit

> **In short:** AgentSeek standardizes the development workflow around generated
> apps without owning their runtime.

## Context

AI app templates can differ in runtime, frontend, environment variables, and
local services.

Developers still need the same basic workflow: create, check, run, inspect, and
extend.

## Lifecycle map

| Stage | Goal | Primary command | Detailed page |
| --- | --- | --- | --- |
| Create | Generate an editable app from a maintained template. | `agentseek create` | [Create a Project](../guides/create-project.md) |
| Inspect | Understand services, entry points, environment checks, and tasks. | `agentseek info` | [Inspect a Project](../guides/inspect-project.md) |
| Configure | Fill required environment values and install project dependencies. | project tools | [Get Started](../get-started/index.md) |
| Check | Verify local readiness before starting services. | `agentseek doctor` | [Check a Project](../guides/check-project.md) |
| Run | Start or preview the template-defined local workflow. | `agentseek dev` | [Run Local Development](../guides/run-local-development.md) |
| Extend | Add or adjust project-defined lifecycle tasks. | `agentseek task` | [Run Project Tasks](../guides/run-project-tasks.md) |

After `agentseek create`, most lifecycle commands should run from the generated
project root. The generated project owns the `.agentseek/lifecycle.toml` file
that tells AgentSeek which services, checks, and tasks exist.

## How it works

AgentSeek provides the command surface. Each generated project provides the
lifecycle behavior.

```text
stable command
  -> project lifecycle spec
    -> template-specific behavior
```

## Why it is like this

The command surface stays predictable across templates.

The generated app keeps control of its runtime details. That makes templates
free to evolve without adding a new AgentSeek command for every runtime choice.

## Consequences for users

- You use the same AgentSeek commands across templates.
- You inspect and change app behavior inside the generated project.
- You use `agentseek task` when a template exposes extra project tasks.
- You can read the [lifecycle spec reference](../reference/lifecycle-spec.md)
  when you need exact field semantics.
