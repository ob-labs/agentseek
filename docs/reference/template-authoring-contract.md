---
title: Template Authoring Contract
type: reference
audience: [A2, A3]
runs: no
verified_on: 2026-07-28
sources:
  - https://github.com/agentseek-ai/agentseek-templates/blob/main/CONTRIBUTING.md
  - https://github.com/agentseek-ai/agentseek-templates/blob/v0.1.0/templates/index.json
  - src/agentseek/cli/lifecycle/spec.py
  - specs/lifecycle-v2-service-discovery.md
---

# Template Authoring Contract

Requirements for new or substantially revised templates. Framework-specific
implementations may differ, but the generated project must preserve this
AgentSeek-facing contract.

New template work belongs in
[`agentseek-ai/agentseek-templates`](https://github.com/agentseek-ai/agentseek-templates).
The core repository's `templates/` tree is a frozen lifecycle-v1 compatibility
mirror for published 0.0.x clients and does not accept normal template feature
development.

## Required Structure

| Path | Requirement | Evidence |
| --- | --- | --- |
| `templates/<type>/<name>/cookiecutter.json` | Always. Defines render inputs and defaults. | Template discovery in `test_templates_render.py`. |
| `templates/<type>/<name>/README.md` | Always. Describes the source template and its render inputs. | `test_registered_templates_have_readme`. |
| `templates/<type>/<name>/{{cookiecutter.project_slug}}/` | Always. Contains the generated project. | Cookiecutter render test. |
| Generated `pyproject.toml` | Always for bundled Python templates. Must contain a non-empty project name and valid dependency list. | `test_template_renders_without_unrendered_jinja`. |
| Generated `.agentseek/lifecycle.toml` | Always. Declares template identity and local lifecycle behavior. | Render and lifecycle smoke tests. |
| Generated `.env.example` | Required when runtime configuration is read from environment variables. | Generated README and lifecycle declarations. |
| Generated `README.md` | Always. Provides the complete first successful run path. | Render review and template smoke coverage. |

## Registry

| Field | Requirement |
| --- | --- |
| Key | `type/name`, matching the template directory and lifecycle `template` value. |
| Description | One sentence describing the generated app and its distinguishing capability. |
| Source of truth | `templates/index.json` in the standalone catalog. Every catalog template directory must be registered. |
| New type | Requires explicit CLI and test review; adding a directory alone is insufficient. |

## Provider Configuration

| Variable | When required | Contract |
| --- | --- | --- |
| `AGENTSEEK_MODEL` | Any template that selects a hosted chat model. | Primary template-facing model setting. Compatibility aliases may be accepted. |
| `AGENTSEEK_API_KEY` | A single OpenAI-compatible credential can configure the runtime. | Primary portable credential. Runtime code may adapt it to the SDK variable. |
| `AGENTSEEK_API_BASE` | A custom OpenAI-compatible endpoint is supported. | Primary portable endpoint setting. Empty means the provider default. |
| `AGENTSEEK_MODEL_PROVIDER` | Multiple native providers are supported. | Selects the provider adapter. The model value must match the selected provider. |
| Provider-native keys | The selected SDK requires a distinct credential, such as `ANTHROPIC_API_KEY` or `GOOGLE_API_KEY`. | Allowed conditionally. `.env.example`, lifecycle checks, runtime code, and README must use the same name and precedence. |

Canonical `AGENTSEEK_*` settings are the public template interface when the
concept applies. Framework-native variables remain adapters or compatibility
aliases; they do not create a second undocumented configuration path.

## Lifecycle Declaration

| Section | Requirement |
| --- | --- |
| Root fields | `version = 2`, exact nonblank `template = "type/name"`, nonblank `name`, useful `description`, project-relative `guide`, and `env_file = ".env"` when environment checks are declared. |
| `[tools]` | Every executable required before setup or local development. |
| `[paths]` | Generated files or installed directories required by `agentseek doctor`. |
| `[env.<name>]` | Configuration that `agentseek doctor` must check. Aliases must match runtime aliases. |
| `[services.<name>]` | Every stable local endpoint, with `name`, `kind`, `display`, `primary`, `description`, optional `tech`, and useful typed `links`. Exactly one non-hidden service is primary. |
| `[processes.<name>]` | Every long-running process started by `agentseek dev`. At least one process is required; use `provides` when same-ID inference is insufficient. |
| `[checks.<name>]` | HTTP readiness check for each checkable service; use `service` when same-ID inference is insufficient. |
| `[tasks.<name>]` | One-shot setup, preparation, or maintenance action exposed by `agentseek task`. Each task has a description; use `starts` and `stops` for service effects. |

`display` is a presentation hint only: `default` is shown first, `advanced` is
available on demand, and `hidden` is omitted from default actions. It does not
control authentication, authorization, network exposure, or startup.

Each catalog template also carries internal `_agentseek_source_url` and
`_agentseek_source_ref` Cookiecutter values. They must point to the reviewed
core repository and exact dependency snapshot recorded by the catalog release;
normal template changes must not replace them with the catalog repository or a
mutable branch.

Environment resolution for lifecycle checks:

```text
lifecycle default < env_file < shell environment
```

Lifecycle defaults and `.env` values validate readiness. AgentSeek does not
inject them into child processes. Process commands must load their runtime
environment themselves.

## Task Names

| Task | Requirement |
| --- | --- |
| `sync` | Installs Python or backend dependencies when a separate install step is required. New templates use `sync`, not framework-specific alternatives such as `backend`. |
| `frontend` | Installs frontend dependencies when the project contains a separate frontend dependency tree. |
| `models` | Downloads or converts local model artifacts when required before development. |
| `<service>` | Prepares or starts an optional dependency that is not fully owned by `agentseek dev`, for example `seekdb`. |
| `ingest-sample` | Loads deterministic sample content when the template demonstrates an ingestion workflow. |
| `<integration>-skills` | Installs an optional external skill pack. The task remains discoverable through `agentseek task --list`. |

Generated READMEs use `agentseek task <name>` for setup. Raw package-manager
commands may explain the implementation, but they are not a parallel primary
workflow.

## Local Services And Networking

| Capability | Requirement |
| --- | --- |
| Development stack | `agentseek dev` starts all long-running processes needed for the documented local experience. |
| Default binding | Backend and frontend servers bind to loopback by default. |
| Remote development | Host overrides are available and documented when remote access is supported. |
| Browser API URL | A frontend derives the backend host from the browser location or accepts an explicit public API URL. It does not hard-code a loopback backend for remote clients. |
| No frontend | Backend-only templates state that no frontend is provided and identify the supported entry point. |

## Optional Capabilities

| Capability | Required disclosure |
| --- | --- |
| Knowledge base | State whether ingestion runs from local files, a server endpoint, a UI, or a lifecycle task. Include one supported sample. |
| Observability | State whether tracing is available, how it is enabled, and which backend receives it. Do not imply that every template supports LangSmith. |
| Local models | Document artifact preparation, supported device settings, and the lifecycle task that prepares models. |
| Conversational response | Default prompts include `Answer in the same language as the user's question.` unless a documented product requirement overrides it. |

## README Contract

| Document | Required contents |
| --- | --- |
| Source template README | Purpose, architecture summary, Cookiecutter inputs, generated layout, and contributor-facing implementation notes. |
| Generated README | Prerequisites, `.env` configuration, ordered lifecycle tasks, `agentseek doctor`, `agentseek dev`, service entry points, optional capabilities, and remote binding when supported. |
| Missing capability | State explicitly when a commonly expected capability is absent, such as a frontend or observability integration. |
| Deviations | Add `Deviations from the template contract` only when an exception exists. Name the rule, reason, user impact, and substitute validation. |

## Exceptions

| Requirement | Contract |
| --- | --- |
| Justification | Framework or runtime constraint, not contributor preference. |
| Documentation | Generated README records the deviation. |
| Pull request | PR description repeats the deviation and its user impact. |
| Evidence | Tests or smoke checks demonstrate the supported alternative. |

## Verification

| Check | Command or evidence |
| --- | --- |
| Full catalog contract | Run `make check` in the standalone catalog checkout. |
| Registry and self-containment | Catalog tests require an exact registry/tree match, regular files/directories only, and a self-contained subtree. |
| Default render and lifecycle smoke | Catalog tests render every registered template and validate strict lifecycle v2 with the paired core snapshot. |
| Generated project inspection | Render the local template with `agentseek create <absolute-template-path> --no-input`. |
| Core documentation | Run `make docs-test` in the AgentSeek core checkout when this contract changes. |

## Related

- [Create a Template](../guides/create-template.md)
- [Lifecycle Spec](lifecycle-spec.md)
- [Templates](templates.md)
