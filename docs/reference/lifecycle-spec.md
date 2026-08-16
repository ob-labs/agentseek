---
title: Lifecycle Spec
type: reference
audience: [A2]
runs: no
verified_on: 2026-08-17
sources:
  - src/agentseek/cli/lifecycle/spec.py
  - src/agentseek/cli/lifecycle/environment.py
  - src/agentseek/cli/lifecycle/dotenv_adapter.py
  - src/agentseek/cli/lifecycle/compatibility.py
  - src/agentseek/cli/lifecycle/core.py
  - src/agentseek/cli/commands/dev.py
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/commands/info.py
  - src/agentseek/cli/lifecycle/authored.py
  - src/agentseek/cli/lifecycle/normalize.py
  - src/agentseek/cli/lifecycle/json_output.py
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
| `agentseek-ai/agentseek-templates` | The locked `v0.1.0` standalone catalog supplies new `version = 2` templates. |
| Normalized and machine surfaces | V1 and v2 project into one safe normalized model; `info --json` and `doctor --json` expose public schema version `1`. |

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
| `env_file` | Optional project-local dotenv file resolved once by `agentseek dev` for declared checks and long-running child processes. |
| `tools` | Required executables used by the project. |
| `paths` | Required local files or directories. |
| `env.<name>` | Environment variables AgentSeek should check. Defaults are lower priority than `env_file` and shell variables. |
| `services.<name>` | Public local service endpoints shown by `agentseek info`. |
| `processes.<name>` | Long-running commands started by `agentseek dev`. |
| `checks.<name>` | Live HTTP readiness checks used by `agentseek doctor --live`. 2xx and 3xx responses are successful. |
| `tasks.<name>` | One-shot tasks run by `agentseek task <name>`. `cwd` is project-relative and must exist. |

For lifecycle v2 HTTP checks, `timeout` is a finite number of seconds greater
than `0` and no greater than `300`; `attempts` is a positive integer.

## Environment Checks

AgentSeek resolves one immutable snapshot per non-dry-run `agentseek dev`
invocation. It captures the launch environment once, then creates the snapshot
from the project `env_file` and non-empty captured launch environment values:

```text
lifecycle env_file < non-empty captured launch environment
```

Bounded python-dotenv resolves physical bindings in order and falls back to the
captured launch environment. In a lifecycle dotenv, `KEY=` is a present empty
assignment, while bare `KEY` assigns nothing. An empty raw launch value is
omitted before the snapshot is created, so a dotenv value can fill it.

Readiness, the internal preflight, and every long-running child consume the
same snapshot. Lifecycle defaults may satisfy readiness but never enter the
snapshot. Only declared `[env.<name>]` keys and aliases participate in
readiness checks. AgentSeek guarantees only the initial child environment/snapshot,
which contains resolved values, not source paths, provenance, or instructions
to repeat resolution. Compatible child configuration completion may fill absent
keys but must not replace inherited present keys. Arbitrary child code can
mutate its own process environment; the prohibition against
duplicated override-loading is an authoring rule, not an AgentSeek enforcement
claim. `agentseek task` does not inherit lifecycle `env_file`; its behavior is
unchanged.

Lifecycle processes using the API completion contract require
`agentseek-api >= 0.2.2`. `agentseek dev --dry-run` prints the plan without
reading the lifecycle dotenv. The missing, undecodable, or malformed dotenv
guarantee applies only to non-dry-run `agentseek dev`: it creates no partial
snapshot, starts no child, and returns `exit 2` with a value-free diagnostic;
bare `KEY` remains valid syntax. Standalone `agentseek info` reports dotenv status without
creating a snapshot. Standalone `agentseek doctor --strict`
renders readiness failures, such as a missing dotenv, and returns `exit 1`.

## Lifecycle v1 first-phase scope

Version 1 supports required tools, required paths, project environment
requirements, HTTP live checks, long-running processes, and one-shot tasks.
It does not support optional tool/path checks, TCP checks, process env
overrides, or multiple env files. It adds no lifecycle-schema interpolation
mode: for a configured `env_file`, bounded python-dotenv resolves physical
bindings in order and falls back to the captured launch environment.

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
| `agentseek info [--verbose] [--json]` | Prints project facts, or emits deterministic safe lifecycle metadata as JSON. |
| `agentseek doctor [--live] [--strict] [--json]` | Checks tools, paths, env, and optional live endpoints; JSON is incompatible with `--strict`. |
| `agentseek dev [--dry-run] [--skip-check]` | Prints or starts declared development processes. `--skip-check` skips only the preliminary strict `doctor` pass. |
| `agentseek task --list` | Lists tasks declared under `tasks`. |
| `agentseek task <name>` | Runs a declared one-shot task. |

## Errors

| Condition | Result |
| --- | --- |
| Missing `.agentseek/lifecycle.toml` | Exit code `2`. |
| Unsupported lifecycle spec version | Exit code `2`. |
| Invalid lifecycle spec | Exit code `2`. |
