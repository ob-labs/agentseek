---
title: Templates
type: reference
audience: [A1, A2]
runs: no
verified_on: 2026-06-23
sources:
  - templates/index.json
  - src/agentseek/cli/commands/create.py
---

# Templates

## Available Templates

| Template | Description |
| --- | --- |
| `bub/default` | Lightweight Bub project with AgentSeek `dev`, `info`, and `doctor` lifecycle tasks. |

## Template Specs

| Form | Example |
| --- | --- |
| Type | `bub` |
| Type and name | `bub/default` |
| Absolute local path | `/path/to/template` |
| Git URL | `https://github.com/example/templates.git` |

## Selection And Discovery

| Command | Result |
| --- | --- |
| `agentseek create` | Select the type and template interactively. |
| `agentseek create --list-templates` | List all known templates. |
| `agentseek create bub --list-templates` | List only `bub` templates. |
| `agentseek create bub` | Resolve to `bub/default`. |
| `agentseek create bub/default` | Use the specific template. |
| `agentseek create bub --template default` | Use `bub/default`. |
| `agentseek create --template` | Compatibility entry point that lists templates. Prefer `--list-templates` in new scripts. |
