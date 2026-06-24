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
env_file = ".env"

[tools]
required = ["uv", "node", "npm"]

[paths]
required = ["frontend/package.json", "frontend/node_modules"]

[env.BUB_MODEL]
required = true
default = "openai:gpt-4o-mini"

[env.BUB_API_KEY]
required = true
aliases = ["BUB_OPENAI_API_KEY"]

[services.app]
url = "http://127.0.0.1:5173"

[processes.frontend]
command = ["npm", "run", "dev"]
cwd = "frontend"

[checks.frontend]
type = "http"
target = "http://127.0.0.1:5173"
timeout = 2
attempts = 3

[tasks.frontend]
description = "Install frontend dependencies."
command = ["npm", "install", "--prefix", "frontend"]
```

## Sections

| Section | Purpose |
| --- | --- |
| `env_file` | Optional project-local env file used only for declared environment checks. It is not injected into child processes. |
| `tools` | Required executables used by the project. |
| `paths` | Required local files or directories. |
| `env.<name>` | Environment variables AgentSeek should check. Defaults are lower priority than `env_file` and shell variables. |
| `services.<name>` | Public local service endpoints shown by `agentseek info`. |
| `processes.<name>` | Long-running commands started by `agentseek dev`. |
| `checks.<name>` | Live HTTP readiness checks used by `agentseek doctor --live`. 2xx and 3xx responses are successful. |
| `tasks.<name>` | One-shot tasks run by `agentseek task <name>`. `cwd` is project-relative and must exist. |

## Environment Checks

AgentSeek checks environment requirements from lifecycle defaults, the optional
`env_file`, and the current process environment:

```text
lifecycle default < env_file < shell environment
```

Only keys declared under `[env.<name>]` and their aliases are read from
`env_file`. Templates do not need to declare every runtime variable a project
may use. AgentSeek does not pass the env file or lifecycle defaults to child
processes.

## First Phase Scope

Version 1 supports required tools, required paths, project environment
requirements, HTTP live checks, long-running processes, and one-shot tasks.
It does not support optional tool/path checks, TCP checks, process env
overrides, multiple env files, or env interpolation.

## Public Commands

| Command | Behavior |
| --- | --- |
| `agentseek info [--verbose]` | Prints project facts from the lifecycle spec. |
| `agentseek doctor [--live] [--strict]` | Checks tools, paths, env, and optional live endpoints. |
| `agentseek dev [--dry-run] [--skip-check]` | Prints or starts declared development processes. `--skip-check` skips only the preliminary strict `doctor` pass. |
| `agentseek task --list` | Lists tasks declared under `tasks`. |
| `agentseek task <name>` | Runs a declared one-shot task. |

## Errors

| Condition | Result |
| --- | --- |
| Missing `.agentseek/lifecycle.toml` | Exit code `2`. |
| Unsupported lifecycle spec version | Exit code `2`. |
| Invalid lifecycle spec | Exit code `2`. |
