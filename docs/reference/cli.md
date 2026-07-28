---
title: CLI Reference
type: reference
audience: [A2]
runs: no
verified_on: 2026-07-28
sources:
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/catalog.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/create.py
  - src/agentseek/cli/commands/dev.py
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/commands/info.py
  - src/agentseek/cli/commands/task.py
  - src/agentseek/data/catalog-lock.json
---

# CLI Reference

## Installation And Invocation

| Command | Description |
| --- | --- |
| `uv tool install agentseek` | Install the CLI for daily use. |
| `agentseek ...` | Run lifecycle commands after installation. |
| `uvx agentseek ...` | Run one AgentSeek command without installing the tool. |

## Root Options

| Option | Description |
| --- | --- |
| `--mode [cli\|agent]` | Select the CLI profile. The documented lifecycle workflow uses `cli`. |
| `--help` | Show help for the selected profile. |

## Default Commands

| Command | Description |
| --- | --- |
| `agentseek create [spec]` | Create a project from a template. |
| `agentseek doctor` | Check local readiness through the lifecycle spec. |
| `agentseek dev` | Start local development through the lifecycle spec. |
| `agentseek info` | Show project metadata and entry points. |
| `agentseek task` | Run project-defined lifecycle spec tasks. |
| `agentseek version` | Show AgentSeek version information. |

## `create`

### Forms

| Form | Description |
| --- | --- |
| `agentseek create` | Select the type and template interactively. |
| `agentseek create <type>` | Use the default template for the type. |
| `agentseek create <type>/<name>` | Use a specific template. |
| `agentseek create <url-or-absolute-path>` | Pass the spec directly to Cookiecutter. |

The built-in template type set is currently `bub`, `deepagents`, and
`langchain`.

### Options

| Option | Description |
| --- | --- |
| `spec` | Template type, `type/name`, Git URL, or absolute local path. |
| `--list-templates` | List templates. With a `type`, list only that type. |
| `--filter keyword` | Filter listed templates by template spec or description. |
| `--template name` | Select a template under the chosen type, for example `bub --template default`. |
| `--template` | Compatibility entry point that lists templates. Prefer `--list-templates` in new scripts. |
| `--template-repo <https-url>` | Select an explicit AgentSeek catalog repository containing `templates/index.json`. Requires `--checkout` with a 40-character lowercase commit SHA. Cannot be combined with a positional direct Cookiecutter URL or absolute path. |
| `--checkout ref` | For a direct Cookiecutter source, use a branch, tag, or commit. With `--template-repo`, the value must match `[0-9a-f]{40}`. |
| `--output-dir path` | Write the generated project below the selected directory. Defaults to the current working directory. |
| `--no-input` | Skip Cookiecutter variable prompts and use template defaults. |
| `--describe` | Print template description and Cookiecutter variables without generating a project. |

### Catalog Source Rules

`--checkout` has three distinct modes:

| Mode | `--checkout` behavior |
| --- | --- |
| Direct Cookiecutter source | A branch, tag, or commit is passed through to Cookiecutter together with the positional URL/path and optional template directory. |
| Named/default AgentSeek catalog | Without `--template-repo`, the embedded catalog lock is the default. An optional ref is an explicit development override in the standalone catalog; the local core v1 mirror is not selected automatically. |
| Explicit AgentSeek catalog override | With `--template-repo`, the value is required and must be an exact 40-character lowercase commit SHA. List, filter, describe, and create all use that immutable coordinate. |

| Input | Resolution rule |
| --- | --- |
| List, filter, or interactive selection without `--template-repo` | Read the registry snapshot embedded in the installed wheel; no network request is needed. |
| Named template or describe without `--template-repo` | Fetch or reuse only the template recorded by the embedded immutable catalog lock. |
| Named template, list, filter, or describe with `--template-repo` and a valid immutable `--checkout` | Use the same explicit catalog repository and commit for every operation. |
| Positional URL or absolute path | Pass the source directly to Cookiecutter without changing its existing URL/path behavior. |
| `--template-repo` with a positional direct Cookiecutter URL or absolute path | Reject the conflicting sources. |
| Explicit catalog repository, checkout, registry, or template failure | Return an error; do not fall back to bundled templates or a local checkout. |

Explicit catalog cache entries are keyed by normalized repository URL and exact
commit. Matching cache metadata is required before reuse. Bundled locked-cache
reuse also requires the selected template bytes to match the trusted digest in
the installed wheel.

AgentSeek 0.1.0 locks the default catalog to
[`agentseek-ai/agentseek-templates` v0.1.0](https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0)
at commit `494863bc1b9aab19f9885d716c03ce654fb26014`. Generated project dependencies
remain pinned independently to the core snapshot `core-snapshot-v0.1.0` at
`883addad1e2993c4be6fc8ba053f87f25fb5057a`. A download or validation failure
is an error; the CLI does not fall back to mutable `main`, the local core v1
mirror, or another catalog revision.

`--list-templates`, `--filter`, and `--describe` inspect catalog content and do
not execute Cookiecutter hooks. Generation trusts the selected template content
and may execute its Cookiecutter hooks. Generated `_agentseek_source_url`
remains the AgentSeek core repository, not the template catalog repository.

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
| `--json` | Emit one schema-versioned JSON document for static and optional live diagnostic results. |

`--strict` and `--json` are mutually exclusive. In JSON mode, a completed
doctor run uses `ok: true` even when a check fails; `data.passed` and the process
exit status report the diagnostic result. Handled JSON output is written only
to stdout.

## `dev`

| Option | Description |
| --- | --- |
| `--dry-run` | Print the startup plan without launching services. |
| `--skip-check` | Skip the preliminary strict `doctor` pass before startup. Core required inputs are still enforced. |

## `info`

| Option | Description |
| --- | --- |
| `--verbose` | Show lifecycle loader discovery details. |
| `--json` | Emit one schema-versioned JSON document with normalized project, service, check, task, reference, and action metadata. |

`info` prints services, environment status, lifecycle task names and
descriptions, and next-step commands for the current project.

JSON output uses public schema version `1`, is deterministic for identical
normalized input, and excludes environment values, raw commands, unsafe URLs,
and absolute host paths. Lifecycle v1 remains supported with
`metadata_complete: false`; lifecycle v2 exposes the complete service topology.
`--verbose` does not add diagnostic prose when combined with `--json`.

See [Lifecycle v2 Service Discovery](lifecycle-v2-service-discovery.md) for the
normative DTO, error, ordering, and exit-status contract.

## `task`

| Form | Description |
| --- | --- |
| `agentseek task --list` | List project-defined lifecycle spec tasks. |
| `agentseek task --help` | Show the AgentSeek task boundary. |
| `agentseek task <name>` | Run a project-defined lifecycle spec task. |

`task` must run from a project directory containing `.agentseek/lifecycle.toml`.
