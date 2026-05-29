---
title: Templates reference
type: reference
audience: [A2]
runs: no
verified_on: 2026-05-28
sources:
  - templates/index.json
  - templates/bub/default/README.md
  - templates/langchain/default/README.md
  - templates/langchain/cli-remote/README.md
  - templates/deepagents/default/README.md
---

# Templates reference

Bundled cookiecutter templates used by `agentseek create`. The catalogue lives
in `templates/index.json`; each template is a cookiecutter project under
`templates/<framework>/<name>/`.

## Catalogue

| Spec | Framework | Name | Description |
| --- | --- | --- | --- |
| `bub/default` | `bub` | `default` | Lightweight Bub agent: `agentseek gateway` + CopilotKit frontend, no LangChain. |
| `langchain/default` | `langchain` | `default` | LangChain `create_agent` + CopilotKit middleware over `agentseek-langchain`. |
| `langchain/cli-remote` | `langchain` | `cli-remote` | Remote LangGraph CLI agent bridged via `LangGraphClientRunnable`. |
| `deepagents/default` | `deepagents` | `default` | Local `create_deep_agent` runnable bound to `agentseek-langchain`. |

Listing comes from `templates/index.json`.

## `agentseek create` argument shapes

| Form | Meaning |
| --- | --- |
| `agentseek create bub` | Default template for the framework (`bub/default`). |
| `agentseek create langchain/cli-remote` | Specific `type/name` spec. |
| `agentseek create langchain --template cli-remote` | Equivalent named-template form. |
| `agentseek create <git-url>` | Fetch a remote cookiecutter; combine with `--checkout`. |
| `agentseek create <local-path>` | Use a local cookiecutter directory. |
| `agentseek create <type> --list-templates` | List templates for the type and exit. |

See `cli.md#agentseek-create-spec` for the full flag table.

## Per-template inputs

### `bub/default`

Mirrors `examples/ag-ui`. Generates an AG-UI gateway plus a CopilotKit-based
frontend.

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Project / directory name. |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `gateway_port` | Default port for `agentseek gateway`. |
| `frontend_port` | Vite dev server port for the frontend. |

### `langchain/default`

Mirrors `examples/ag_ui_langchain`. Generates a `create_agent` project with
CopilotKit middleware bound to agentseek via `agentseek-langchain`.

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name. |
| `author` | Project author. |
| `system_prompt` | System prompt baked into the agent. |
| `default_model` | Default `AGENTSEEK_MODEL`. |

### `langchain/cli-remote`

Mirrors `examples/langchain_cli_remote_agent`. Runs a graph via
`langgraph dev` and bridges it through `LangGraphClientRunnable`.

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name. |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `langgraph_url` | Default LangGraph Agent Server URL. |
| `assistant_id` | Graph / assistant id (matches `langgraph.json`). |

### `deepagents/default`

Mirrors `examples/langchain_deepagents`. Local `create_deep_agent(...)`
runnable bound to agentseek via `agentseek-langchain`.

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name (auto-derived). |
| `author` | Project author. |
| `system_prompt` | System prompt baked into the agent. |
| `default_model` | Default `AGENTSEEK_MODEL`. |

## See also

- How-to: [How to install a plugin](../how-to/install-a-plugin.md)
- Tutorial: [02 — Build your first harness app](../tutorials/02-first-harness-app.md)
- Reference: [CLI reference](cli.md)
