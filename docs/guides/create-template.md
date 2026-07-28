---
title: Create a Template
type: how-to
audience: [A2, A3]
runs: yes
verified_on: 2026-07-28
sources:
  - https://github.com/agentseek-ai/agentseek-templates/blob/main/CONTRIBUTING.md
  - https://github.com/agentseek-ai/agentseek-templates/blob/v0.1.0/templates/index.json
  - src/agentseek/cli/commands/create.py
  - specs/lifecycle-v2-service-discovery.md
---

# Create a Template

Use this guide in the standalone
[`agentseek-ai/agentseek-templates`](https://github.com/agentseek-ai/agentseek-templates)
repository. Do not add new templates to the core repository's frozen
lifecycle-v1 compatibility mirror. Read the
[Template Authoring Contract](../reference/template-authoring-contract.md)
before choosing configuration names or lifecycle tasks.

## Prerequisites

- A local standalone catalog checkout with `uv sync` completed.
- A clear generated-app outcome and one existing template with a similar runtime.
- A unique `type/name` spec. Reuse `bub`, `deepagents`, or `langchain` unless the contribution also extends CLI type support.

## 1. Inspect The Closest Template

List the public templates.

```bash
uv run agentseek create --list-templates
```

Inspect the render inputs for the closest template.

```bash
uv run agentseek create langchain/agentic-rag --describe
```

Copy only the structure needed by the new app. Keep framework-specific runtime
details inside the generated project.

## 2. Create The Template Tree

Use this layout:

```text
templates/<type>/<name>/
  cookiecutter.json
  README.md
  {{cookiecutter.project_slug}}/
    .agentseek/lifecycle.toml
    .env.example
    README.md
    pyproject.toml
```

Add application source, frontend files, Compose files, and other assets below
the generated project directory only when the app needs them.

## 3. Define Render Inputs

Start `cookiecutter.json` with stable identity fields and only the choices a
contributor should decide at render time.

```json title="cookiecutter.json excerpt"
{
  "project_name": "My Agent",
  "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_').replace('-', '_') }}",
  "author": "Your Name",
  "system_prompt": "You are a helpful assistant. Answer in the same language as the user's question.",
  "default_model": "openai:gpt-4o-mini",
  "_agentseek_source_url": "https://github.com/ob-labs/agentseek.git",
  "_agentseek_source_ref": "<catalog-paired-core-commit>"
}
```

Keep runtime-only values in `.env.example`. Do not turn every environment
variable into a Cookiecutter prompt.

## 4. Standardize Provider Configuration

Use the AgentSeek names as the generated app's public configuration when each
concept applies.

```dotenv title=".env.example excerpt"
AGENTSEEK_MODEL={{ cookiecutter.default_model }}
AGENTSEEK_API_KEY=
AGENTSEEK_API_BASE=
```

Add `AGENTSEEK_MODEL_PROVIDER` when the app selects among native provider
adapters. Add provider-specific keys only when the selected SDK requires them.
Document how runtime code maps aliases and which value wins.

Declare the same required names under `[env.*]` in the lifecycle file. AgentSeek
uses those declarations for readiness checks; it does not inject `.env` into
child processes.

## 5. Define The Lifecycle

Declare the generated app's required tools, paths, environment checks, local
services, long-running processes, readiness checks, and setup tasks.

```toml title=".agentseek/lifecycle.toml excerpt"
version = 2
template = "langchain/my-template"
name = "{{ cookiecutter.project_name }}"
description = "LangChain example application."
env_file = ".env"
guide = "README.md"

[tools]
required = ["uv"]

[env.AGENTSEEK_MODEL]
required = true
default = "{{ cookiecutter.default_model }}"
description = "Chat model used by the generated agent."

[services.backend]
name = "LangGraph API"
url = "http://127.0.0.1:2024"
kind = "api"
display = "default"
primary = true
description = "Local API used by the generated application."
links = { docs = "https://docs.langchain.com/oss/python/langgraph/overview" }

[processes.backend]
command = ["uv", "run", "python", "-m", "{{ cookiecutter.project_slug }}.server"]

[checks.backend]
type = "http"
target = "http://127.0.0.1:2024"
timeout = 2
attempts = 3
service = "backend"

[tasks.sync]
description = "Install Python dependencies."
command = ["uv", "sync"]
```

Use `sync` for Python or backend dependencies and `frontend` for a separate
frontend dependency tree. Put all long-running local processes under
`[processes.*]` so `agentseek dev` owns the documented development stack.

Servers bind to loopback by default. If remote development is supported, add
documented host overrides. A browser frontend must derive the backend host from
the browser location or accept an explicit public API URL.

## 6. Write Both README Surfaces

The source template `README.md` covers:

- Generated application purpose and architecture.
- Cookiecutter inputs and defaults.
- Generated directory layout.
- Framework-specific contributor notes.

The generated `README.md` covers:

- Prerequisites and `.env` configuration.
- Ordered `agentseek task` setup commands.
- `agentseek doctor`, `agentseek dev`, and service entry points.
- Frontend availability, knowledge ingestion, observability, local models, and remote binding when applicable.
- Missing expected capabilities, such as no frontend or no observability integration.

Use `Deviations from the template contract` only when a framework constraint
requires an exception. Include the rule, reason, user impact, and substitute
validation.

## 7. Register The Template

Add one `type/name` entry to `templates/index.json`.

```json title="templates/index.json excerpt"
{
  "langchain/my-template": "LangChain example app with AgentSeek lifecycle spec."
}
```

The key must match the template directory and lifecycle `template` value.

## 8. Render The Local Template

Set the spec to the template being checked. The example uses a checked-in
template so the command is directly runnable.

```bash
export TEMPLATE_SPEC=langchain/agentic-rag
```

Create an empty output directory.

```bash
export TEMPLATE_OUTPUT="$(mktemp -d)"
```

Render from the absolute local path with Cookiecutter defaults.

```bash
uv run agentseek create "$PWD/templates/$TEMPLATE_SPEC" --no-input --output-dir "$TEMPLATE_OUTPUT"
```

Inspect the generated `.env.example`, `.agentseek/lifecycle.toml`, README, and
application entry points. Run lifecycle commands from the generated project.

## 9. Run Template Validation

Check the lock, registry, self-containment, every default render, strict
lifecycle-v2 loading, formatting, and linting.

```bash
make check
```

Add a focused CI smoke test when the template depends on model conversion,
external services, hardware-specific libraries, or another integration that
default rendering cannot prove.

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Registry test reports a missing template | `templates/index.json` has no matching key. | Add the exact `type/name` entry; every standalone catalog directory must be registered. |
| Render test finds `{{` in generated files | A Cookiecutter variable is missing or escaped incorrectly. | Add the input to `cookiecutter.json` or correct the generated-file expression. |
| `agentseek doctor` accepts configuration but the process cannot read it | The lifecycle check and runtime loader use different names, or the process never loads `.env`. | Align the names and load runtime configuration in the generated app. |
| Frontend works locally but fails from a remote browser | A server or frontend API URL is fixed to loopback. | Keep loopback as the default and add explicit host/API overrides. |

## Related

- [Template Authoring Contract](../reference/template-authoring-contract.md)
- [Lifecycle Spec](../reference/lifecycle-spec.md)
- [Run Project Tasks](run-project-tasks.md)
