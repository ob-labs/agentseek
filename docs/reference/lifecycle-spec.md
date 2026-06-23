---
title: Lifecycle Spec
type: reference
audience: [A2]
runs: no
verified_on: 2026-06-23
sources:
  - src/agentseek/cli/lifecycle/spec.py
  - src/agentseek/cli/lifecycle/core.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# Lifecycle Spec

## File

AgentSeek discovers the lifecycle spec from the current directory upward:

```text
.agentseek/lifecycle.toml
```

Other project files are outside lifecycle discovery.

## Shape

```toml
version = 1
template = "bub/default"
name = "My Bub Agent"

[tools]
required = ["uv", "node", "npm"]
optional = []

[paths]
required = ["frontend/package.json", "frontend/node_modules"]
optional = []

[env.BUB_MODEL]
required = true

[services.app]
url = "http://127.0.0.1:5173"

[processes.frontend]
command = ["npm", "run", "dev"]
cwd = "frontend"

[checks.frontend]
type = "http"
url = "http://127.0.0.1:5173"
timeout = 2
attempts = 3

[tasks.frontend]
description = "Install frontend dependencies."
command = ["npm", "install", "--prefix", "frontend"]
```

## Sections

| Section | Purpose |
| --- | --- |
| `tools` | Required and optional executables used by the project. |
| `paths` | Required and optional local files or directories. |
| `env.<name>` | Environment variables required or recognized by the project. |
| `services.<name>` | Public local service endpoints shown by `agentseek info`. |
| `processes.<name>` | Long-running commands started by `agentseek dev`. |
| `checks.<name>` | Live readiness checks used by `agentseek doctor --live`. |
| `tasks.<name>` | Optional one-shot tasks run by `agentseek task <name>`. |

## Public Commands

| Command | Behavior |
| --- | --- |
| `agentseek info [--verbose]` | Prints project facts from the lifecycle spec. |
| `agentseek doctor [--live] [--strict]` | Checks tools, paths, env, and optional live endpoints. |
| `agentseek dev [--dry-run] [--skip-check]` | Prints or starts declared development processes. |
| `agentseek task --list` | Lists tasks declared under `tasks`. |
| `agentseek task <name>` | Runs a declared one-shot task. |

## Errors

| Condition | Result |
| --- | --- |
| Missing `.agentseek/lifecycle.toml` | Exit code `2`. |
| Unsupported lifecycle spec version | Exit code `2`. |
| Invalid lifecycle spec | Exit code `2`. |
