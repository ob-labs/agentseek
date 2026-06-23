---
title: CLI Reference
type: reference
audience: [A2]
runs: no
verified_on: 2026-06-23
sources:
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/create.py
  - src/agentseek/cli/commands/chat.py
  - src/agentseek/cli/commands/dev.py
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/commands/info.py
  - src/agentseek/cli/commands/task.py
---

# CLI Reference

## Root Options

| Option | Description |
| --- | --- |
| `--mode [cli\|agent]` | Select the CLI profile. Defaults to `cli`. |
| `--help` | Show help for the selected profile. |

## Default Commands

| Command | Description |
| --- | --- |
| `agentseek create [spec]` | Create a project from a template. |
| `agentseek doctor` | Check local readiness through the project `duties.py`. |
| `agentseek dev` | Start local development through the project `duties.py`. |
| `agentseek info` | Show project metadata and entry points. |
| `agentseek task` | Forward to Duty and run project-defined tasks. |
| `agentseek version` | Show AgentSeek version information. |

## Agent profile

| Form | Description |
| --- | --- |
| `agentseek --mode agent` | Enter the experimental agent profile. Explicit confirmation is required. |
| `agentseek --mode agent --help` | Show agent profile help. |

The `agent` profile currently has no public subcommands.

## `create`

### Forms

| Form | Description |
| --- | --- |
| `agentseek create` | Select the type and template interactively. |
| `agentseek create <type>` | Use the default template for the type. |
| `agentseek create <type>/<name>` | Use a specific template. |
| `agentseek create <url-or-absolute-path>` | Pass the spec directly to Cookiecutter. |

### Options

| Option | Description |
| --- | --- |
| `spec` | Template type, `type/name`, Git URL, or absolute local path. |
| `--list-templates` | List templates. With a `type`, list only that type. |
| `--template name` | Select a template under the chosen type, for example `bub --template default`. |
| `--template` | Compatibility entry point that lists templates. Prefer `--list-templates` in new scripts. |
| `--checkout ref` | Use a branch, tag, or commit when fetching the remote template source. |
| `--no-input` | Skip Cookiecutter variable prompts and use template defaults. |

### Missing Templates

| Form | Behavior |
| --- | --- |
| `agentseek create bub --template missing` | Exits with code `2` and shows the missing template plus supported `bub` templates. |
| `agentseek create bub/missing` | Exits with code `2` and shows the missing template plus supported `bub` templates. |

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

## `info`

| Option | Description |
| --- | --- |
| `--verbose` | Show lifecycle loader discovery details. |

## `task`

| Form | Description |
| --- | --- |
| `agentseek task --list` | List project-defined Duty tasks. |
| `agentseek task --help` | Show the AgentSeek forwarding boundary; inside a project, forward to Duty. |
| `agentseek task <name>` | Run a project-defined Duty task. |
| `agentseek task <name> key=value` | Pass parameters to a Duty task. |

`task` must run from a project directory containing `duties.py`. Duty parses `--list` and task-specific parameters.
