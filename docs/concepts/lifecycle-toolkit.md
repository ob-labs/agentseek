---
title: Lifecycle Toolkit
type: explanation
audience: [A2, A5]
runs: no
verified_on: 2026-06-22
sources:
  - README.md
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
