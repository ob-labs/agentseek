---
title: Desktop Service Discovery and Lifecycle v2
type: explanation
audience: [A2, A3]
runs: no
verified_on: 2026-07-21
sources:
  - src/agentseek/cli/lifecycle/spec.py
  - src/agentseek/cli/lifecycle/core.py
  - src/agentseek/cli/lifecycle/errors.py
  - src/agentseek/cli/commands/info.py
  - src/agentseek/cli/commands/doctor.py
  - docs/reference/lifecycle-spec.md
  - templates/index.json
  - "templates/bub/contextseek/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/deepagents/content-builder/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/deepagents/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/deepagents/research/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/deepagents/sandbox/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/agentic-rag/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/agentic-rag-openvino/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/cli-remote/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - tests/cli_commands/test_lifecycle.py
  - tests/cli_commands/test_templates_render.py
---

# Desktop Service Discovery and Lifecycle v2

> **In short:** Add a compact lifecycle v2 authoring format and a separate,
> deterministic JSON discovery contract. Templates describe what each service
> is, which service users normally open, and how services relate to processes,
> checks, and tasks. AgentSeek normalizes that input into an explicit model for
> Desktop and other consumers without exposing commands or secrets.

## Status

This document is the accepted design contract for AgentSeek 0.1.0. It does not
change current CLI or template behavior by itself; implementation and release
verification remain separate work.

The design discussion is
[GitHub Discussion #133](https://github.com/ob-labs/agentseek/discussions/133).

## Context

Successful template startup currently prints a collection of endpoints, but an
endpoint alone does not say whether it is:

- a browser application;
- an API or agent protocol endpoint;
- a developer tool such as LangGraph Studio or Phoenix;
- a database connection string; or
- an internal dependency that should not be presented as the next step.

The distinction matters for both people and software. A person needs a clear
"open this" result. AgentSeek Desktop needs structured, stable data from which
it can render actions and retain project metadata for later use.

Lifecycle v1 cannot represent these semantics. Its service model contains only
a name, URL, and optional description, while checks and processes are separate
maps with no explicit relationship. Human-oriented `agentseek info` output is
not a suitable machine contract because its wording and layout may evolve.

## Goals

1. Make the primary browser entry point unambiguous.
2. Explain non-browser services and provide useful references.
3. Give Desktop a deterministic, versioned JSON contract.
4. Keep template authoring compact through schema-defined conventions.
5. Represent every current template topology without heuristics.
6. Preserve lifecycle v1 and existing human-readable CLI behavior.
7. Prevent discovery output from exposing secrets or executable commands.

## Non-goals

- Starting services directly from `agentseek info`.
- Replacing `agentseek dev`, lifecycle tasks, or `agentseek doctor`.
- Treating a presentation hint as access control or network policy.
- Inferring semantics from ports, environment-variable names, service names,
  descriptions, or framework names.
- Adding JSON output to every lifecycle command in the first change.
- Emitting a live JSON event stream from `agentseek dev`.

## Design overview

The design has three layers:

1. **Authored lifecycle:** a compact TOML format for template maintainers.
2. **Normalized project model:** one explicit internal representation for v1
   and v2 inputs.
3. **Public DTO:** a stable JSON schema for Desktop and other integrations.

The public DTO is intentionally more explicit than the authored TOML. Compact
authoring must not require consumers to reproduce AgentSeek's normalization
rules.

## Authored lifecycle v2

### Root fields

```toml
version = 2
template = "langchain/markdown-messages"
name = "Markdown Messages"
description = "Local LangGraph application with a browser frontend."
env_file = ".env"
guide = "README.md"
```

| Field | Required | Meaning |
| --- | --- | --- |
| `version` | yes | Must be `2` for this schema. |
| `template` | yes | Nonblank stable template identifier. |
| `name` | yes | Nonblank generated-project name. |
| `description` | no | Project-level explanation; defaults to null. |
| `env_file` | no | Same project-relative environment file used by v1 checks. |
| `guide` | no | Project-relative guide to present alongside discovery data. |

`guide` must be a relative path that resolves inside the project root. Absolute
paths and traversal outside the project root are invalid.

V2 retains the v1 `tools`, `paths`, and `env` sections unchanged:

| Field | Type | Meaning |
| --- | --- | --- |
| `tools.required` | string array | Required bare executable names. |
| `paths.required` | string array | Required project-relative paths. |
| `env.<id>.required` | boolean | Whether the declared variable is required. |
| `env.<id>.default` | string or null | Check-only default; never exported or serialized. |
| `env.<id>.description` | string | Safe explanation of the requirement. |
| `env.<id>.aliases` | string array | Alternative variable names. |

V2 also retains the v1 requirement that at least one process is declared.
Unknown TOML fields remain invalid.

### Process, check, and task fields

V2 extends the existing section models rather than replacing them:

| Section field | Required | Meaning |
| --- | --- | --- |
| `processes.<id>.command` | yes | Existing nonempty command string array. |
| `processes.<id>.cwd` | no | Existing project-relative working directory. |
| `processes.<id>.provides` | no | Complete explicit service list; absent uses the same-ID convention. |
| `checks.<id>.type` | no | Existing `http` type; defaults to `http`. |
| `checks.<id>.target` | yes | Existing literal HTTP readiness target. |
| `checks.<id>.timeout` | no | Existing timeout in seconds. |
| `checks.<id>.attempts` | no | Existing positive attempt count. |
| `checks.<id>.service` | conditional | Explicit service when no same-ID service exists. |
| `tasks.<id>.command` | yes | Existing nonempty command string array. |
| `tasks.<id>.cwd` | no | Existing project-relative working directory. |
| `tasks.<id>.description` | no | Existing human explanation. |
| `tasks.<id>.starts` | no | Complete explicit list of services started by the task. |
| `tasks.<id>.stops` | no | Complete explicit list of services stopped by the task. |

Lifecycle v2 does not add environment interpolation. Service URLs, check
targets, and reference URLs are literal values in the generated lifecycle file.
Bundled template sources may use Cookiecutter expressions, but generation must
resolve them before AgentSeek loads `.agentseek/lifecycle.toml`. The discovery
projection never expands an environment variable.

Every v2 path-bearing field—`guide`, `env_file`, each `paths.required` value,
and every process or task `cwd`—must be relative to the project root, contain no
NUL or `..` segment, and remain inside the project root after resolution.
Immediately before any filesystem access, AgentSeek resolves the project root
and candidate with `strict=False` and requires the candidate to be relative to
the resolved root. Existing symlinks are followed during this check, so a
symlink that escapes the project is rejected. `.` remains valid for `cwd`.

Every v2 `tools.required` value is a bare executable name matching
`^[A-Za-z0-9][A-Za-z0-9._+-]*$`. Absolute paths, path separators, whitespace,
NUL/control characters, `.` and `..`, and CLI-option-like leading hyphens are
invalid. AgentSeek may pass only validated bare names to executable lookup.

V2 rejects duplicate values in `tools.required` and `paths.required`. V1 keeps
loading duplicate declarations, but JSON normalization retains the first exact
occurrence and emits a deterministic `duplicate_requirement_collapsed` warning
for each later occurrence.

### Service fields

```toml
[services.frontend]
name = "Application"
url = "http://127.0.0.1:5174"
kind = "web"
display = "default"
primary = true
description = "Browser application for this template."
tech = "vite"
links = { docs = "https://vite.dev/guide/" }
```

| Field | Required | Values and meaning |
| --- | --- | --- |
| `name` | yes | Human-readable name, nonblank after trimming. |
| `url` | yes | Literal absolute endpoint in the generated lifecycle file. |
| `kind` | yes | `web`, `api`, `protocol`, `database`, or `other`. |
| `display` | no | `default`, `advanced`, or `hidden`; defaults to `default`. |
| `primary` | no | Whether this is the normal first entry point; defaults to `false`. |
| `description` | yes | Nonblank explanation of the service's purpose. |
| `tech` | no | Display-only technology label such as `ag-ui` or `langgraph`. |
| `links` | no | Compact map of typed reference URLs. |

Initial link relations are:

- `docs`: framework or protocol documentation;
- `api_docs`: service-specific API documentation;
- `studio`: an interactive development or inspection tool.

`tech` and link relations are labels, not behavioral signals. Actions are
derived only from validated service fields and explicit relationships.

### What `display` means

`display` is a presentation hint:

- `default`: show in the normal project summary;
- `advanced`: show under developer details;
- `hidden`: omit from ordinary discovery views, while retaining the service in
  the normalized topology and diagnostic output.

`display` must never control authentication, authorization, port binding,
network exposure, secret handling, or whether a process is started. In
particular, `hidden` does not make an endpoint private or secure.

### Primary service rules

Every v2 project that declares services must declare exactly one primary
service. The primary service:

- must have `primary = true`;
- must not use `display = "hidden"`;
- may be any kind, because API-only templates have no browser UI.

A browser-based template normally marks its `web` service as primary. An
API-only template marks the endpoint that best represents successful startup.

A v2 project that declares no services is valid and has no primary service. It
may contain processes and tasks, but `provides`, check-to-service associations,
`starts`, and `stops` cannot name services that do not exist.

### Compact relationship conventions

Most templates already use the same identifier for a service and its process or
check. Lifecycle v2 makes that convention normative:

- `processes.<id>` provides `services.<id>` when both exist.
- `checks.<id>` checks `services.<id>` when both exist.
- tasks never imply service effects.

Only exceptions need annotations:

```toml
[processes.stack]
command = ["docker", "compose", "up"]
provides = ["gateway", "copilotkit", "frontend", "phoenix", "seekdb"]

[checks.custom_routes]
target = "http://127.0.0.1:2024/custom-routes"
service = "backend"

[tasks.phoenix]
description = "Start Phoenix and its database."
command = ["docker", "compose", "up", "-d", "phoenix"]
starts = ["phoenix", "phoenix_seekdb"]

[tasks.phoenix-stop]
description = "Stop Phoenix and its database."
command = ["docker", "compose", "down"]
stops = ["phoenix", "phoenix_seekdb"]
```

Relationship semantics are:

- If `provides` is absent, same-ID process-to-service association applies.
- If `provides` is present, it is the complete association for that process;
  no same-ID association is added implicitly.
- If `service` is absent, same-ID check-to-service association applies.
- A check without a same-ID service must declare `service`.
- `starts` and `stops` are complete, explicit task effects.
- A service may have zero, one, or multiple providers and checks.
- Multiple providers are valid; for example, a database may be started by
  `agentseek dev` or by a standalone task.

All referenced service identifiers must exist. V2 service, process, check,
task, and environment identifiers are case-sensitive and must match
`^[A-Za-z0-9][A-Za-z0-9_-]*$`. This excludes whitespace, control characters,
dots, path separators, and CLI-option-like leading hyphens. V1 identifiers stay
loadable without applying the new grammar.

### Example: Bub

```toml
version = 2
template = "bub/default"
name = "Bub Agent"
guide = "README.md"

[services.app]
name = "Application"
url = "http://127.0.0.1:5173"
kind = "web"
display = "default"
primary = true
description = "Browser application for this template."

[services.gateway]
name = "AG-UI gateway"
url = "http://127.0.0.1:8088/agent"
kind = "protocol"
display = "advanced"
description = "AG-UI endpoint used by the application runtime."
tech = "ag-ui"
links = { docs = "https://docs.ag-ui.com/introduction" }

[services.copilotkit]
name = "CopilotKit runtime"
url = "http://127.0.0.1:4000/api/copilotkit"
kind = "api"
display = "hidden"
description = "Internal CopilotKit runtime used by the frontend."
tech = "copilotkit"
links = { docs = "https://docs.copilotkit.ai/concepts/architecture" }

[processes.frontend]
command = ["npm", "run", "dev"]
provides = ["app", "copilotkit"]

[checks.frontend]
target = "http://127.0.0.1:5173"
service = "app"
```

The gateway uses the same identifier as its process and check, so it needs no
relationship annotations.

### Example: typical LangGraph template

```toml
[services.backend]
name = "LangGraph API"
url = "http://127.0.0.1:2024"
kind = "api"
display = "advanced"
primary = false
description = "LangGraph development API used by the frontend."
tech = "langgraph"
links = { docs = "https://docs.langchain.com/oss/python/langgraph/overview", api_docs = "http://127.0.0.1:2024/docs", studio = "https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024" }

[services.frontend]
name = "Application"
url = "http://127.0.0.1:5174"
kind = "web"
display = "default"
primary = true
description = "Browser application for this template."
```

Because `backend` and `frontend` identifiers align across services, processes,
and checks, no relationship annotations are needed.

## Validation and safe projection

Lifecycle v2 is rejected if any of these conditions hold:

- `template` or `name` is blank;
- services are declared and zero or more than one service has `primary = true`;
- the single primary service, when present, is hidden;
- a service name is blank after trimming;
- a required description is blank after trimming;
- an identifier violates the v2 grammar;
- a relationship refers to an unknown service;
- a check has neither an explicit service nor a same-ID service;
- any path-bearing field is absolute, contains `..`, or resolves outside the
  project root through lexical traversal or a symlink;
- a required tool is not a validated bare executable name;
- `tools.required` or `paths.required` contains an exact duplicate;
- an endpoint or link uses an unsafe scheme;
- a URL contains user information, a disallowed query, or a fragment;
- an endpoint, target, or reference contains an unresolved `${...}` or
  `{{ ... }}` placeholder.

Allowed endpoint schemes are:

| Service kind | Allowed schemes |
| --- | --- |
| `web` | `http`, `https` |
| `api` | `http`, `https`, `ws`, `wss` |
| `protocol` | `http`, `https`, `ws`, `wss` |
| `database` | `mysql` |
| `other` | `http`, `https`, `ws`, `wss`, `mysql` |

Every service URL and HTTP check target must be absolute. Service endpoints and
check targets may not contain user information, a query, or a fragment. The
validator applies these rules to the literal authored value; it never reads or
substitutes environment values. Because the initial check type is `http`, check
targets accept only `http` or `https` schemes.

Reference validation is relation-specific:

| Relation | Allowed URL shape |
| --- | --- |
| `docs` | Absolute `https` URL without user information, query, or fragment. |
| `api_docs` | Absolute `https` URL, or `http` on `127.0.0.0/8`, `::1`, or `localhost`; no user information, query, or fragment. |
| `studio` | Absolute `https` URL without user information or fragment. It may contain only one `baseUrl` query parameter. |

When `studio` has `baseUrl`, its decoded value must itself be an absolute safe
`http` or `https` endpoint without user information, query, or fragment. No
other reference query parameters are accepted. This allowlist avoids relying on
credential-name heuristics, including percent-encoded variants such as
`api_key`, `access_token`, or `signature`.

V2 validation is deliberately strict because a rejected template can be fixed
before release. V1 input remains loadable. During v1 projection, AgentSeek emits
a service URL only when it is absolute, uses `http`, `https`, `ws`, `wss`, or
`mysql`, and has no user information, query, fragment, or unresolved
placeholder. A v1 HTTP check target additionally must use `http` or `https`.
Any unsafe v1 service URL or check target value is omitted in full: the owning
service or check remains in normalized output, its `url` or `target` is null,
and AgentSeek emits an `unsafe_endpoint_omitted` warning. AgentSeek never
attempts partial redaction.

An unsafe v1 HTTP check remains represented in `CheckDefinitionDTO` with a
null target. Without `--live`, its doctor result is `not_run`. With `--live`,
AgentSeek never sends the request and returns a project-scoped result with ID
`service-check:<check-id>`, type `http`, state `fail`, message
`Unsafe endpoint was not checked.`, and target null. This failed result makes
`doctor --live --json` exit with status 1 while keeping `ok: true`.

JSON-mode v1 path projection applies the same root-confinement check as v2.
Unsafe path values are never accessed or serialized and produce an
`unsafe_path_omitted` warning. In `doctor --json`, an unsafe v1 `env_file`,
required path, process `cwd`, or required tool also produces a project-scoped
failed result with target null. V1 required tools that do not satisfy the v2
bare-name rule are never passed to executable lookup.

| Source | Result ID | Type | Fixed message |
| --- | --- | --- | --- |
| `env_file` | `unsafe-path:env-file` | `env_file` | `Unsafe project path was not checked.` |
| `paths.required` item | `unsafe-path:required:<zero-based-index>` | `path` | `Unsafe project path was not checked.` |
| Process `cwd` | `unsafe-path:process-cwd:<zero-based-index>` | `process_cwd` | `Unsafe project path was not checked.` |
| `tools.required` item | `unsafe-path:required-tool:<zero-based-index>` | `tool` | `Unsafe executable requirement was not checked.` |

Required-path and required-tool indices use authored array positions. Process
indices use the position after sorting process IDs in ascending Unicode code
point order.
An unsafe v1 task `cwd` produces the warning only because `info` and `doctor`
do not execute tasks. This safe JSON behavior does not change legacy human
output or task execution in the initial compatibility release.

## Normalized project model

The loader uses distinct authored models, `LifecycleSpecV1` and
`LifecycleSpecV2`. Both are projected into one internal normalized model.

`LifecycleSpecV1` preserves the current field set and validation exactly.
`LifecycleSpecV2` uses the exhaustive v2 fields defined above. Version
dispatch happens after TOML decoding but before model validation, so v2-only
rules never reject an otherwise valid v1 project.

For v2, normalization expands all conventions into explicit relationships and
validates the result. For v1:

- project `template` and `name` are retained, while project `description` and
  `guide` are null;
- service `name`, `description`, `kind`, `display`, `primary`, and `tech` are
  null;
- relationship collections are empty;
- every v1 check has `service_id: null` and remains unassociated;
- no action is inferred;
- no semantics are inferred from a name, URL, port, or description;
- `metadata_complete` is `false` and warnings explain the limitation.

This boundary lets the public JSON contract remain stable while template
authors migrate incrementally.

## Public JSON contract

### Commands

The initial machine-readable surface is:

- `agentseek info --json`: declared discovery metadata only;
- `agentseek doctor --json`: static diagnostic results;
- `agentseek doctor --live --json`: static and live check results.

Without `--json`, current human-readable output remains unchanged.

`agentseek info --verbose --json` is valid, but `--verbose` does not change the
DTO because JSON mode always emits the complete discovery model.
`agentseek doctor --strict --json` is rejected with the structured
`cli_option_conflict` error and exit status 2. JSON consumers receive every raw
result and apply their own warning policy; projection warnings such as
`lifecycle_v1_metadata_incomplete` are not readiness failures.

### Common envelope

After the CLI parser recognizes `--json`, every success and failure writes
exactly one JSON document to stdout. Unknown options and malformed command-line
syntax that prevent `--json` from being recognized retain Typer's normal usage
error behavior.

JSON examples in this document are pretty-printed for review. Wire output uses
the compact serialization defined under Determinism.

```json
{
  "schema_version": 1,
  "command": "info",
  "ok": true,
  "lifecycle_version": 2,
  "data": {},
  "error": null
}
```

| Field | Type | Contract |
| --- | --- | --- |
| `schema_version` | integer | Public DTO version; initially `1`. |
| `command` | string | `info` or `doctor`. |
| `ok` | boolean | Whether AgentSeek handled and completed the command. |
| `lifecycle_version` | integer or null | Parsed lifecycle version when known. |
| `data` | object or null | Command DTO on handled success. |
| `error` | object or null | Error DTO on handled failure. |

Exactly one of `data` and `error` is non-null. A doctor result that completes
but finds a failed check has `ok: true`, a non-null `data`, and `error: null`.

`schema_version` versions the public DTO independently of lifecycle TOML.
Removing a field, changing requiredness or nullability, changing an enum, or
changing an identifier rule requires a schema-version increment. Additive
nullable fields may be introduced within a version. Consumers must ignore
unknown object fields but must reject unsupported `schema_version` values.

### `info` data DTO

`data` has these required fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `project` | `ProjectDTO` | Project identity and guide. |
| `metadata_complete` | boolean | `true` for valid v2; `false` for v1. |
| `environment` | `EnvironmentRequirementDTO[]` | Declared requirement metadata. |
| `services` | `ServiceDTO[]` | Explicit normalized service topology. |
| `checks` | `CheckDefinitionDTO[]` | Declared service checks, not results. |
| `tasks` | `TaskDTO[]` | Safe task metadata and effects. |
| `actions` | `ActionDTO[]` | Derived safe user actions. |
| `warnings` | `WarningDTO[]` | Compatibility or safe-projection warnings. |

`ProjectDTO`:

| Field | Type | Notes |
| --- | --- | --- |
| `template` | string or null | Stable authored template ID; null only when absent in v1. |
| `name` | string | Current lifecycle project name. |
| `description` | string or null | Current lifecycle description. |
| `guide` | `ProjectFileDTO` or null | Safe project-relative guide. |

`ProjectFileDTO` contains required `path` and `rel` fields. `rel` is `guide` in
schema version 1. It never contains an absolute host filesystem path.

`EnvironmentRequirementDTO`:

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Environment variable name. |
| `required` | boolean | Whether it is required. |
| `description` | string or null | Safe authored description. |
| `aliases` | string array | Declared alternative names. |

Environment values and defaults are never included.

`ServiceDTO`:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Lifecycle service identifier. |
| `name` | string or null | Required for v2; null for v1. |
| `description` | string or null | Required for v2; nullable for v1. |
| `url` | string or null | Safe literal authored endpoint or null. |
| `kind` | enum or null | V2 service kind; null for v1. |
| `display` | enum or null | V2 presentation hint; null for v1. |
| `primary` | boolean or null | V2 primary marker; null for v1. |
| `tech` | string or null | Display-only label. |
| `providers` | `ProviderDTO[]` | Explicit provider relationships. |
| `check_ids` | string array | Associated declared check identifiers. |
| `links` | `ReferenceDTO[]` | Validated typed references. |

`ProviderDTO`:

| Field | Type | Notes |
| --- | --- | --- |
| `type` | enum | `dev` or `task`. |
| `id` | string | Stable provider identifier. |
| `process_id` | string or null | Process used by `agentseek dev`. |
| `task_id` | string or null | Lifecycle task that starts the service. |

Exactly one of `process_id` and `task_id` is non-null. Stop tasks are lifecycle
actions, not providers; their relationships are retained in `TaskDTO.stops`.
Provider identifiers are `process:<process_id>` and `task:<task_id>`.

`CheckDefinitionDTO`:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Check identifier. |
| `service_id` | string or null | Associated v2 service; null for v1. |
| `type` | string | `http` in schema version 1. |
| `target` | string or null | Safe target endpoint. |
| `state` | string | Always `not_run` in `info`. |

`TaskDTO`:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Task identifier. |
| `description` | string or null | Authored task description. |
| `starts` | string array | Explicit services started. |
| `stops` | string array | Explicit services stopped. |

Raw task and process commands are never included.

`ReferenceDTO` contains required `rel` and `url` strings. `rel` uses the
authored link vocabulary. The URL has passed safe-projection validation.

`ActionDTO`:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Stable action identifier. |
| `type` | enum | `open_url`, `copy_endpoint`, `open_reference`, `start_dev`, or `run_task`. |
| `label` | string | Human-readable action label. |
| `service_id` | string or null | Related service. |
| `url` | string or null | Safe endpoint or reference. |
| `reference_rel` | string or null | Reference relation. |
| `task_id` | string or null | Task invoked by `run_task`. |

The field relevant to the action type is non-null; unrelated fields are null.
Consumers do not reconstruct actions from service metadata.

Action identifiers, labels, and populated fields are normative:

| Type | ID | Label | Non-null relationship fields |
| --- | --- | --- | --- |
| `open_url` | `service:<service_id>:open` | `Open <service.name>` | `service_id`, `url` |
| `copy_endpoint` | `service:<service_id>:copy` | `Copy <service.name> endpoint` | `service_id`, `url` |
| `open_reference` | `service:<service_id>:reference:<rel>` | `Open <service.name> <rel>` | `service_id`, `url`, `reference_rel` |
| `start_dev` | `project:start_dev` | `Start development` | none |
| `run_task` | `task:<task_id>` | `Run task <task_id>` | `task_id` |

### Action derivation

AgentSeek derives actions during normalization:

| Input | Derived action |
| --- | --- |
| `web` with `default` or `advanced` display | `open_url` |
| `api`, `protocol`, or `database` with non-hidden display | `copy_endpoint` |
| Any validated reference on a non-hidden service | `open_reference` |
| Any process provider on a non-hidden service | one global `start_dev` action |
| Any explicit task effect on at least one non-hidden service | `run_task` |
| Hidden service | no default action |
| Lifecycle v1 | no actions |

An `other` service receives no endpoint action in schema version 1. Explicit
references and providers may still produce actions when it is non-hidden.

The global `start_dev` action is emitted once even when multiple services have
process providers. A `run_task` action is emitted once per task, even when that
task affects multiple services; its `service_id` is null and the service effects
remain available on `TaskDTO`. Actions are presentation-safe suggestions; the
CLI remains the authority that validates and executes a task.

### `doctor` data DTO

`doctor` data has these required fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `passed` | boolean | Whether all executed checks passed. |
| `live_requested` | boolean | Whether `--live` was supplied. |
| `results` | `CheckResultDTO[]` | Static and declared live checks. |
| `warnings` | `WarningDTO[]` | Safe-projection or compatibility warnings. |

`CheckResultDTO`:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Stable check identifier. |
| `scope` | enum | `project` or `service`. |
| `service_id` | string or null | Set for service-scoped checks. |
| `type` | enum | `lifecycle`, `tool`, `path`, `env_file`, `env`, `process_cwd`, or `http`. |
| `state` | enum | `not_run`, `pass`, or `fail`. |
| `message` | string | Safe result summary. |
| `target` | string or null | Safe target when applicable. |

A static or live result uses these normative IDs:

| Result | ID | Scope |
| --- | --- | --- |
| Lifecycle file | `lifecycle:spec` | `project` |
| Required tool | `tool:<tool-name>` | `project` |
| Required path | `path:<project-relative-path>` | `project` |
| Environment file | `env-file:<project-relative-path>` | `project` |
| Environment requirement | `env:<env-id>` | `project` |
| Process working directory | `process-cwd:<process-id>` | `project` |
| Declared HTTP check | `service-check:<check-id>` | `service` for associated v2 checks; otherwise `project` |

The normalized result array requires unique IDs. Exact duplicate v1 tool or
path requirements are collapsed to the first occurrence before checks run;
v2 rejects them during validation. Map-backed environment, process, and check
IDs are unique by construction. Unsafe-path result IDs use source indices and
therefore cannot collide with safe result IDs.

For project-scoped results `service_id` is null. A v1 HTTP check is
project-scoped because v1 has no authored service association.

A declared live check returned by `doctor --json` without `--live` has state
`not_run`. `passed` is false when any executed result is `fail`; `not_run`
results are excluded from that calculation. The DTO deliberately defines no
aggregate service-health field. Absence of a check is not interpreted as
health.

### Warnings and errors

`WarningDTO` contains required fields in `code`, `message`, `details` order.
Messages and detail shapes are normative:

| Code | Fixed message | `details` keys in order |
| --- | --- | --- |
| `lifecycle_v1_metadata_incomplete` | `Lifecycle v1 metadata is incomplete.` | `{}` |
| `unsafe_endpoint_omitted` | `Unsafe endpoint was omitted.` | `owner_type`, `owner_id`, `field` |
| `unsafe_path_omitted` | `Unsafe project path was omitted.` | `owner_type`, `owner_id`, `index`, `field` |
| `duplicate_requirement_collapsed` | `Duplicate requirement was collapsed.` | `requirement_type`, `first_index`, `duplicate_index` |

For `unsafe_endpoint_omitted`, `owner_type` is `service` or `check`,
`owner_id` is the authored map key, and `field` is `url` or `target`. For
`unsafe_path_omitted`, `owner_type` is `env_file`, `required_path`,
`required_tool`, `process`, or `task`; `owner_id` and `index` are nullable when
not applicable; `field` is `env_file`, `path`, `tool`, or `cwd`. Duplicate
detail indices are zero-based and `requirement_type` is `tool` or `path`.
Warning details never contain the omitted endpoint, path, or executable value.

A handled error uses this envelope:

```json
{
  "schema_version": 1,
  "command": "info",
  "ok": false,
  "lifecycle_version": null,
  "data": null,
  "error": {
    "code": "lifecycle_not_found",
    "message": "No lifecycle.toml was found.",
    "details": {}
  }
}
```

Initial stable error codes are:

- `cli_option_conflict`;
- `lifecycle_not_found`;
- `lifecycle_toml_invalid`;
- `lifecycle_validation_failed`;
- `lifecycle_version_unsupported`;
- `internal_error`.

`ErrorDTO` always contains `code`, `message`, and `details`. Initial messages
and detail shapes are:

| Code | Fixed message | `details` shape |
| --- | --- | --- |
| `cli_option_conflict` | `Options --strict and --json cannot be combined.` | `{ "options": ["--json", "--strict"] }` |
| `lifecycle_not_found` | `No lifecycle.toml was found.` | `{}` |
| `lifecycle_toml_invalid` | `The lifecycle TOML is invalid.` | `{ "line": integer or null, "column": integer or null }` |
| `lifecycle_validation_failed` | `The lifecycle specification is invalid.` | `{ "issues": [{ "path": string, "code": string, "message": string }] }` |
| `lifecycle_version_unsupported` | `The lifecycle version is unsupported.` | `{ "found": integer or null, "supported": [1, 2] }` |
| `internal_error` | `Unexpected internal error.` | `{}` |

Validation issues are sorted by `path`, then `code`, then `message`. Issue
messages identify the violated rule but never echo the rejected input value.
No error message or details may include exception text, raw commands,
environment values, credentials, absolute host paths, or unsafe URLs.

### Exit status and streams

| Condition | Exit status | JSON `ok` |
| --- | --- | --- |
| Successful `info` | 0 | true |
| Doctor completes and all executed checks pass | 0 | true |
| Doctor completes and a check fails | 1 | true |
| Unexpected internal failure after `--json` is recognized | 1 | false |
| `--strict --json` option conflict | 2 | false |
| Missing or invalid lifecycle input | 2 | false |

All JSON-mode rows write one envelope to stdout and nothing to stderr. The
`internal_error` envelope is the final exception boundary for JSON mode. The
implementation may log a traceback only to an explicitly configured private
debug log, never to the JSON streams by default.

### Determinism

Within one AgentSeek release and public `schema_version`, identical normalized
`info` input produces byte-for-byte identical output. Doctor has the same
guarantee for an identical normalized project and identical captured diagnostic
result snapshot. Filesystem, tool, environment, and live-service state are
doctor inputs; changing them may change result content.

Serialization is normative:

- UTF-8 encoding with non-ASCII characters emitted directly;
- compact JSON separators `,` and `:` with no insignificant whitespace;
- object fields in the order shown by the envelope and DTO tables;
- `"` and `\\` escapes for quotation mark and reverse solidus, the short JSON
  escapes for backspace, tab, line feed, form feed, and carriage return, and
  lowercase `\u00xx` escapes for other U+0000–U+001F controls; `/` is not
  escaped;
- exactly one trailing line feed;
- no timestamps, durations, random identifiers, or absolute host paths.

Array ordering is normative:

| Array | Sort key |
| --- | --- |
| `environment` | `name`, ascending Unicode code point order |
| `services`, `checks`, `tasks`, `actions`, doctor `results` | `id`, ascending Unicode code point order |
| `providers` | `(type, id)` |
| service `links` | `(rel, url)` |
| warning arrays | `(code, message, canonical serialized details)` |
| validation issues | `(path, code, message)` |
| `aliases`, `check_ids`, `starts`, `stops`, supported versions | scalar value ascending |

Maps from authored TOML are always projected to these sorted arrays. Adding an
allowed nullable field in a later AgentSeek release may change bytes without
changing `schema_version`; semantic compatibility still follows the versioning
rules above.

## Security boundary

Discovery is a projection, not serialization of the authored lifecycle file.
The public DTO must not contain:

- environment values or defaults;
- raw process, task, setup, or hook commands;
- shell fragments or expanded command arguments;
- absolute guide paths;
- environment-expanded URL content;
- URL user information, endpoint queries, fragments, or reference queries not
  explicitly allowed for `studio.baseUrl`;
- unsafe v1 endpoints that cannot be redacted without changing their meaning.

V2 rejects unsafe input at validation time and never evaluates `${...}`.
V1 remains compatible and omits the entire unsafe field with a warning. This
makes `info --json` safe for local persistence and ordinary support output,
subject to the same care as other project metadata.

## Current-template migration

The repository currently contains eleven registered lifecycle templates and one
quarantined `bub/contextseek` lifecycle file. They fit the model as follows:

| Template | Primary | Key exceptions or migration note |
| --- | --- | --- |
| `bub/contextseek` | `app` | Quarantined; frontend process/check map to `app`; gateway and CopilotKit are supporting services. |
| `bub/default` | `app` | Frontend process/check map to `app`; gateway is protocol; CopilotKit is hidden API. |
| `deepagents/content-builder` | `frontend` | LangGraph backend is advanced API. |
| `deepagents/default` | AG-UI endpoint | API-only template; protocol endpoint is primary. |
| `deepagents/research` | `frontend` | Same-ID conventions cover frontend and LangGraph backend. |
| `deepagents/sandbox` | `frontend` | Same-ID conventions cover frontend and LangGraph backend. |
| `langchain/agentic-rag` | `frontend` | Add the omitted seekdb service; retain both the `seekdb` dev process and `tasks.seekdb` provider with `starts = ["seekdb"]`. |
| `langchain/agentic-rag-hybrid` | `frontend` | `custom_routes` checks backend; Phoenix and Phoenix seekdb are task-started. |
| `langchain/agentic-rag-openvino` | `frontend` | seekdb has dev and task providers but no HTTP check. |
| `langchain/cli-remote` | LangGraph API | API-only template; API endpoint is primary. |
| `langchain/default` | `frontend` | `stack` explicitly provides five services; seekdb has no HTTP check. |
| `langchain/markdown-messages` | `frontend` | Same-ID conventions cover frontend and backend. |

This audit found 31 declared services and 28 declared service checks. Nine
registered templates have browser frontends, two are intentionally API-only,
and the quarantined template follows the Bub pattern. All mismatches are covered
by `provides`, `service`, `starts`, or `stops`; no template-specific parsing is
required.

## Compatibility and delivery sequence

The implementation should be delivered in these contract-preserving slices.
Repository ownership, catalog resolution, and cross-repository release order
remain governed by
[ADR 0001](../docs/adr/0001-versioned-template-catalog-boundary.md):

1. Add separate v1 and v2 authored models plus normalized internal DTOs.
2. Add v2 validation, safe projection, relationship normalization, and action
   derivation without changing human output.
3. Add versioned `info --json` and `doctor [--live] --json` DTOs.
4. Establish the standalone template catalog, copy and migrate registered
   templates there, retain the core templates as the lifecycle-v1 compatibility
   mirror, then validate the quarantined template independently.
5. Add the immutable catalog lock and standalone-catalog resolver defined by
   [ADR 0001](../docs/adr/0001-versioned-template-catalog-boundary.md).
6. Update human next-step output only in a separate reviewed change, using the
   same normalized model rather than a second set of rules.

Lifecycle v1 remains readable. V1 JSON is deliberately conservative and marked
incomplete; consumers must not mistake inferred metadata for an authored
contract.

## Verification requirements

Implementation is not complete without tests proving:

- v1 loads through the distinct v1 model and retains current human output;
- valid v2 files normalize same-ID and explicit relationships correctly;
- a service-free v2 project is valid with no primary, while every nonempty
  service map requires exactly one non-hidden primary;
- zero, multiple, and task-only providers are represented;
- services with no check are not reported healthy;
- invalid primary, relationship, identifier, path, and URL cases fail with
  stable errors;
- v2 rejects user information, endpoint queries, fragments, unresolved
  placeholders, and all non-allowlisted reference queries, including encoded
  credential-like keys;
- v2 rejects absolute, traversal, and symlink-escaping path fields; JSON-mode
  v1 projection never accesses or serializes them and returns the specified
  warnings and failed doctor results;
- v2 accepts only bare required-tool names; JSON-mode v1 projection never
  looks up or serializes unsafe executable paths;
- v2 rejects duplicate tool/path requirements; v1 collapses them with unique
  diagnostic IDs and canonical warnings;
- blank service names and non-HTTP check targets fail v2 validation;
- v1 unsafe endpoints are omitted with warnings; unsafe live-check targets
  produce a null-target `not_run` result without `--live`, are never requested
  with `--live`, and then produce the specified failed doctor result;
- v1 service names and check associations remain null rather than inferred;
- environment values/defaults and raw commands never appear in JSON;
- hidden services produce no actions and `display` affects no execution path;
- every action is derived exactly once and respects service display;
- all public DTO fields, nullability, enums, and ordering match this spec;
- handled errors emit one JSON document on stdout with empty stderr;
- unexpected JSON-mode exceptions emit a redacted `internal_error` envelope;
- `doctor --strict --json` emits `cli_option_conflict` and exit status 2;
- doctor check failures use exit status 1 with `ok: true`;
- static and live doctor results use the normative IDs and scopes;
- repeated `info --json` output is byte-for-byte identical;
- every registered standalone template renders and validates as lifecycle v2;
- every registered core compatibility template still renders and loads as
  lifecycle v1, while quarantined sources retain their quarantine behavior;
- rendered-template tests cover relationship integrity after Cookiecutter
  rendering and prove that lifecycle loading performs no environment
  interpolation.

Golden JSON fixtures should cover one representative v1 template, one typical
same-ID v2 template, Bub's mismatched frontend mapping, the hybrid task-started
Phoenix services, `agentic-rag` with dev and task seekdb providers, and the
single-process `langchain/default` stack.

## Consequences for users

People get a clear first action while advanced endpoints remain available with
short explanations and reference links. Desktop gets structured data that can
be stored and rendered without parsing terminal prose. Template maintainers add
only the service semantics and exceptional relationships; common topology stays
compact. Existing lifecycle v1 projects keep working, but their machine metadata
is explicitly incomplete until they adopt v2.

## Related

- [ADR 0001: Versioned Standalone Template Catalog](../docs/adr/0001-versioned-template-catalog-boundary.md)
- [AG-UI introduction](https://docs.ag-ui.com/introduction)
- [CopilotKit architecture](https://docs.copilotkit.ai/concepts/architecture)
- [LangGraph documentation](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangSmith Studio](https://docs.langchain.com/oss/python/langgraph/studio)
- [Phoenix documentation](https://arize.com/docs/phoenix)
