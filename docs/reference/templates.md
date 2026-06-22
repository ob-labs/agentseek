---
title: Templates
type: reference
audience: [A1, A2]
runs: no
verified_on: 2026-06-22
sources:
  - templates/index.json
  - src/agentseek/cli/commands/create.py
---

# Templates

## Available templates

| Template | Description |
| --- | --- |
| `bub/default` | Lightweight Bub project with lifecycle tasks. |

## Template spec forms

| Form | Example |
| --- | --- |
| Type | `bub` |
| Type and name | `bub/default` |
| Local path | `/path/to/template` |
| Git URL | `https://github.com/example/templates.git` |

## Selection

| Command | Result |
| --- | --- |
| `agentseek create` | Interactive selection. |
| `agentseek create bub` | Resolve to `bub/default`. |
| `agentseek create bub/default` | Use a specific template path. |
| `agentseek create --template` | List templates. |
