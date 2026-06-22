---
title: CLI Reference
type: reference
audience: [A2]
runs: no
verified_on: 2026-06-22
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/create.py
  - src/agentseek/cli/commands/dev.py
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/commands/info.py
  - src/agentseek/cli/commands/task.py
---

# CLI Reference

## Commands

| Command | Description |
| --- | --- |
| `agentseek create [spec]` | Scaffold a project from a template. |
| `agentseek doctor` | Check readiness through the project lifecycle file. |
| `agentseek dev` | Run local development through the project lifecycle file. |
| `agentseek info` | Show project metadata and entry points. |
| `agentseek task` | Run project-defined tasks. |
| `agentseek version` | Show AgentSeek version information. |

## `create`

| Option | Description |
| --- | --- |
| `spec` | Template type, template path, URL, or local path. |
| `--template [name]` | Select or list templates under a type. |
| `--checkout ref` | Use a branch, tag, or commit for a remote template. |
| `--list-templates` | List templates for a type. |
| `--no-input` | Use template defaults without prompts. |

## `doctor`

| Option | Description |
| --- | --- |
| `--live` | Check already-running local services. |
| `--strict` | Treat warnings as failures. |

## `dev`

| Option | Description |
| --- | --- |
| `--dry-run` | Print the startup plan without launching services. |
| `--skip-check` | Skip the strict readiness check before startup. |

## `task`

| Form | Description |
| --- | --- |
| `agentseek task --list` | List project-defined tasks. |
| `agentseek task <name>` | Run a project-defined task. |
| `agentseek task <name> key=value` | Pass task arguments. |
