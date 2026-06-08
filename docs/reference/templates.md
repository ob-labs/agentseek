---
title: Templates reference
type: reference
audience: [A2]
runs: no
verified_on: 2026-06-05
sources:
  - templates/index.json
  - templates/bub/default/README.md
  - templates/bub/contextseek/README.md
  - templates/langchain/default/README.md
  - templates/langchain/cli-remote/README.md
  - templates/langchain/markdown-messages/README.md
  - templates/langchain/sandbox/README.md
  - templates/deepagents/default/README.md
  - templates/deepagents/research/README.md
  - templates/deepagents/content-builder/README.md
---

# Templates reference

Bundled cookiecutter templates used by `agentseek create`. The catalogue lives
in `templates/index.json`; each template is a cookiecutter project under
`templates/<framework>/<name>/`.

> **This is a growing collection.** We are continuously adding new templates and
> polishing existing ones — across LangChain, DeepAgents, and Bub. Check back
> or watch the [templates/ directory](https://github.com/ob-labs/agentseek/tree/main/templates)
> for updates. PRs for new templates are welcome.

## Catalogue

| Spec | Framework | Name | Description |
| --- | --- | --- | --- |
| `bub/default` | `bub` | `default` | Lightweight Bub agent: `agentseek gateway` + CopilotKit frontend, no LangChain. |
| `bub/contextseek` | `bub` | `contextseek` | Bub agent with ContextSeek semantic memory layer and ctx HTTP API for feeding and inspecting context. |
| `langchain/default` | `langchain` | `default` | LangChain `create_agent` + CopilotKit middleware over `agentseek-langchain`. |
| `langchain/cli-remote` | `langchain` | `cli-remote` | Remote LangGraph CLI agent bridged via `LangGraphClientRunnable`. |
| `langchain/markdown-messages` | `langchain` | `markdown-messages` | Pure LangChain `create_agent` + `langgraph dev` backend, `useStream` + react-markdown frontend. No agentseek runtime. |
| `langchain/sandbox` | `langchain` | `sandbox` | DeepAgents sandbox coding agent with LangSmith sandbox backend, tool-call cards, and join/rejoin streaming UI. |
| `deepagents/default` | `deepagents` | `default` | Local `create_deep_agent` runnable bound to `agentseek-langchain`. |
| `deepagents/research` | `deepagents` | `research` | Pure DeepAgents research agent with Tavily search and streamed tool/sub-agent UI. |
| `deepagents/content-builder` | `deepagents` | `content-builder` | DeepAgents content builder with brand memory, skills, subagents, image generation, and streamed UI. |

Listing comes from `templates/index.json`.

> **Tip — browse from the terminal.** Run `agentseek create --template` to see
> all templates with descriptions, or `agentseek create langchain --template` to
> filter by framework type.

## Picking a template

Different templates suit different developer profiles and use cases:

| If you are… | Recommended template | Why |
| --- | --- | --- |
| New to LangChain and agents | `langchain/markdown-messages` | Minimal dependencies, 5-minute path from zero to a running chatbot. Add complexity later. |
| A LangChain user wanting full delivery | `langchain/default` | Ships CopilotKit frontend + Feishu IM gateway + agentseek runtime — everything needed to hand a product to stakeholders. |
| Building a sandbox-backed coding agent | `langchain/sandbox` | DeepAgents + LangSmith sandbox with streaming tool-call cards and join/rejoin UI. |
| Building a Deep Research agent | `deepagents/research` | Pre-wired Tavily search, sub-agent delegation, streamed report UI — mirrors the upstream DeepAgents research pattern. |
| Building a content-generation agent | `deepagents/content-builder` | Brand memory, skills, subagents, web search, image generation, and a streamed content UI. |
| Connecting to a remote LangGraph server | `langchain/cli-remote` | Bridges `langgraph dev` via `LangGraphClientRunnable`; useful when the graph runs elsewhere (agentseek-api, LangSmith, etc.). |
| Wanting the lightest harness path (no LangChain) | `bub/default` | Pure Bub kernel + CopilotKit frontend; no LangChain in the dependency tree. |
| Wanting Bub plus semantic memory | `bub/contextseek` | Extends the Bub path with ContextSeek memory, a ctx HTTP API, and a seed script. |
| Integrating LangChain with agentseek runtime | `deepagents/default` | `create_deep_agent` bound to `agentseek-langchain` — both the harness data layer and DeepAgents orchestration. |

## `agentseek create` argument shapes

| Form | Meaning |
| --- | --- |
| `agentseek create --template` | List all templates across all types with descriptions. |
| `agentseek create langchain --template` | List templates for the given type. |
| `agentseek create --list-templates` | List all templates across all types with descriptions. |
| `agentseek create <type> --list-templates` | List templates for the type (same as `--template` with no value). |
| `agentseek create langchain/cli-remote` | Specific `type/name` spec. |
| `agentseek create langchain --template cli-remote` | Equivalent named-template form. |
| `agentseek create bub` | Default template for the framework (`bub/default`). |
| `agentseek create` | Interactive type + template selection. |
| `agentseek create <git-url>` | Fetch a remote cookiecutter; combine with `--checkout`. |
| `agentseek create <local-path>` | Use a local cookiecutter directory. |

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

### `bub/contextseek`

Extends `bub/default` with a ContextSeek semantic memory layer, a ctx HTTP API
server, and a seed script that preloads example knowledge on first boot.

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Project / directory name (auto-derived). |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `gateway_port` | Port for `agentseek gateway`. Defaults to `8088`. |
| `frontend_port` | Vite dev server port for the frontend. Defaults to `5173`. |
| `copilotkit_port` | CopilotKit Express runtime port. Defaults to `4000`. |
| `ctx_server_port` | FastAPI ctx HTTP server port. Defaults to `8089`. |
| `contextseek_storage_backend` | ContextSeek storage backend. Defaults to `seekdb`. |
| `contextseek_storage_path` | Reserved local ContextSeek store path input. |
| `contextseek_tenant` | ContextSeek tenant identifier. Defaults to `default`. |

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

### `langchain/markdown-messages`

Pure LangChain template with no agentseek runtime dependency. Generates a
`create_agent` backend served by `langgraph dev` and a Vite + React frontend
that streams messages via `useStream` and renders them as markdown.

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. Defaults to "Markdown Messages Agent". |
| `project_slug` | Python package / directory name (auto-derived). |
| `author` | Project author. |
| `system_prompt` | System prompt baked into the agent. |
| `default_model` | Model id passed to `init_chat_model(...)`. |
| `langgraph_port` | Backend port for `langgraph dev`. Defaults to `2024`. |
| `frontend_port` | Frontend dev-server port. Defaults to `5174`. |

### `langchain/sandbox`

DeepAgents coding-agent template backed by LangSmith Sandbox. Generates a
`create_deep_agent` backend served by `langgraph dev` plus a React + Vite chat
UI with streaming tool-call cards and join/rejoin support.

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name (auto-derived). |
| `author` | Project author. |
| `default_model_provider` | Default `init_chat_model(..., model_provider=...)` provider. Ships as `openai`. |
| `default_model` | Model id for the selected provider. Defaults to `gpt-4.1-mini`. |
| `langgraph_port` | Backend port for `langgraph dev`. Defaults to `2024`. |
| `frontend_port` | Frontend dev-server port. Defaults to `5175`. |

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

### `deepagents/research`

Pure DeepAgents research template. Scaffolds a `create_deep_agent(...)`
project with Tavily search, sub-agent task delegation, and a streamed
frontend showing tool calls and the final markdown report.

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name (auto-derived). |
| `author` | Project author. |
| `default_model` | Default `init_chat_model("<provider>:<model>")` id. |
| `tavily_max_results` | Default `tavily_search` result limit. |
| `tavily_topic` | Tavily topic filter (`general`, `news`, or `finance`). |
| `max_concurrent_research_units` | Max sub-agent tasks queued concurrently. |
| `max_researcher_iterations` | Max search/reflection loops per research unit. |
| `langgraph_port` | Default backend port for `langgraph dev`. |
| `frontend_port` | Default Vite dev-server port. |

### `deepagents/content-builder`

DeepAgents content writing agent with brand memory, skills, subagents, web
search, and image generation. Generates a LangGraph backend and a Vite + React
frontend that streams tool calls, sub-agent delegation, todos, generated
images, and final markdown output.

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name (auto-derived). |
| `author` | Project author. |
| `default_model_provider` | Default `init_chat_model(..., model_provider=...)` provider. Ships as `openai`. |
| `default_model` | Default model id for the selected provider. Ships empty so the generated app reads `AGENTSEEK_MODEL`. |
| `google_image_model` | Gemini model for image generation. Defaults to `gemini-3.1-flash-image-preview`. |
| `tavily_max_results` | Default web search result limit. |
| `tavily_topic` | Tavily topic filter (`general` or `news`). |
| `langgraph_port` | Default backend port for `langgraph dev`. |
| `frontend_port` | Default Vite dev-server port. |

## After you generate a project — next steps

Once your agent is running, add capabilities from the suite:

| Next step | Component | Docs |
| --- | --- | --- |
| Add persistent memory and semantic retrieval | ContextSeek | [github.com/ob-labs/contextseek](https://github.com/ob-labs/contextseek) |
| Ship the graph as a production API service | agentseek-api | [github.com/ob-labs/agentseek-api](https://github.com/ob-labs/agentseek-api) |
| Switch to OceanBase / seekdb for durable storage | langchain-oceanbase | [github.com/oceanbase/langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) |
| Wire up ContextSeek inside the harness | agentseek-contextseek | [How to use ContextSeek](../how-to/use-contextseek.md) |
| Connect Feishu / DingTalk / Slack | IM Gateway | [How to run the gateway](../how-to/run-gateway.md) |

## See also

- How-to: [How to install a plugin](../how-to/install-a-plugin.md)
- Tutorial: [02 — Build your first harness app](../tutorials/02-first-harness-app.md)
- Reference: [CLI reference](cli.md)
