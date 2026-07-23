---
title: Lifecycle Spec
type: reference
audience: [A2]
runs: no
verified_on: 2026-07-21
sources:
  - src/agentseek/cli/lifecycle/spec.py
  - src/agentseek/cli/lifecycle/core.py
  - src/agentseek/cli/lifecycle/authored.py
  - src/agentseek/cli/lifecycle/safety.py
  - specs/lifecycle-v2-service-discovery.md
  - docs/adr/0001-versioned-template-catalog-boundary.md
  - templates/index.json
  - tests/cli_commands/test_templates_render.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# Lifecycle Spec

## File

AgentSeek discovers the lifecycle spec from the current directory upward:

```text
.agentseek/lifecycle.toml
```

Other project files are outside lifecycle discovery.

## Authored versions and catalog boundary

AgentSeek currently loads and validates authored lifecycle versions `1` and
`2`. The existing human commands and their v1 behavior remain compatible.

| Authored version or location | Current boundary |
| --- | --- |
| `1`, `2` | Authored lifecycle files load and validate. |
| `templates/` | Core remains the `version = 1` compatibility mirror. |
| `agentseek-ai/agentseek-templates` | A later `version = 2` catalog migration. |
| This slice | Implements authored loading and validation only; normalization, JSON, and catalog delivery remain separate work. |

For the complete authored contract, see the published [lifecycle v2 overview
(`lifecycle-v2-service-discovery.md`)](lifecycle-v2-service-discovery.md).
The exact canonical source is
<https://github.com/ob-labs/agentseek/blob/main/specs/lifecycle-v2-service-discovery.md>.

## Lifecycle v1 shape

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

## Lifecycle v1 first-phase scope

Version 1 supports required tools, required paths, project environment
requirements, HTTP live checks, long-running processes, and one-shot tasks.
It does not support optional tool/path checks, TCP checks, process env
overrides, multiple env files, or env interpolation.

## Lifecycle v2 authored fields

V2 retains the v1 `tools`, `paths`, and `env` sections and requires at least
one process. Its root fields are `version`, `template`, and `name`, with
optional `description`, `env_file`, and `guide`; `template` and `name` must be
nonblank. `guide`, `env_file`, `paths.required`, and process/task `cwd` values
must remain project-relative and confined to the project root.

Each `services.<id>` entry has `name`, `url`, `kind`, `display`, `primary`,
`description`, optional `tech`, and typed `links`. `kind` is one of `web`,
`api`, `protocol`, `database`, or `other`; `display` is one of `default`,
`advanced`, or `hidden`. `display` is only a presentation hint: it never
controls authentication, authorization, network exposure, or process startup.

V2 uses same-ID relationships by default: a matching process provides a
service and a matching check checks a service. Use `processes.<id>.provides`,
`checks.<id>.service`, and `tasks.<id>.starts` or `tasks.<id>.stops` for
explicit relationships. Identifiers must use the v2 identifier grammar and
every referenced service must exist. Projects with services require exactly one
non-hidden `primary = true` service; checks require a matching or explicit
service. Validation also rejects unknown fields, empty commands, duplicate
`tools.required` or `paths.required` values, unsafe executable names, paths,
endpoints, and typed reference URLs.

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
