---
title: Template Authoring Contract
type: reference
audience: [A2, A3]
runs: no
verified_on: 2026-07-10
sources:
  - templates/index.json
  - src/agentseek/cli/lifecycle/spec.py
  - src/agentseek/cli/lifecycle/core.py
  - tests/cli_commands/test_templates_registry.py
  - tests/cli_commands/test_templates_render.py
  - "templates/langchain/agentic-rag/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.env.example"
---

# Template Authoring Contract

Requirements for new or substantially revised templates. Framework-specific
implementations may differ, but the generated project must preserve this
AgentSeek-facing contract.

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
| Source of truth | `templates/index.json`. Every non-quarantined Cookiecutter template must be registered. |
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
| Root fields | `version = 1`, exact `template = "type/name"`, human-readable `name`, and `env_file = ".env"` when environment checks are declared. |
| `[tools]` | Every executable required before setup or local development. |
| `[paths]` | Generated files or installed directories required by `agentseek doctor`. |
| `[env.<name>]` | Configuration that `agentseek doctor` must check. Aliases must match runtime aliases. |
| `[services.<name>]` | Every stable user-facing local endpoint shown by `agentseek info`. |
| `[processes.<name>]` | Every long-running process started by `agentseek dev`. At least one process is required. |
| `[checks.<name>]` | HTTP readiness check for each service with a stable health or application endpoint. |
| `[tasks.<name>]` | One-shot setup, preparation, or maintenance action exposed by `agentseek task`. Each task has a description. |

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
| Registry consistency | `uv run python -m pytest tests/cli_commands/test_templates_registry.py -q` |
| Default render and lifecycle smoke | `uv run python -m pytest tests/cli_commands/test_templates_render.py -q` |
| Generated project inspection | Render the local template with `agentseek create <absolute-template-path> --no-input`. |
| Documentation | `make docs-test` |

## Related

- [Create a Template](../guides/create-template.md)
- [Lifecycle Spec](lifecycle-spec.md)
- [Templates](templates.md)
