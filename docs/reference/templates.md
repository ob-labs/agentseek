---
title: Templates reference
type: reference
audience: [A2]
runs: no
verified_on: 2026-06-25
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

## Catalogue

| Spec | Description |
| --- | --- |
| `bub/default` | Lightweight Bub agent: `agentseek gateway` + CopilotKit frontend, no LangChain. |
| `bub/contextseek` | Bub agent with ContextSeek semantic memory layer and ctx HTTP API. |
| `langchain/default` | LangChain `create_agent` + CopilotKit middleware over `agentseek-langchain`, with optional Phoenix/SeekDB OTEL tracing. |
| `langchain/cli-remote` | Remote LangGraph CLI agent bridged via `LangGraphClientRunnable`. |
| `langchain/markdown-messages` | Pure LangChain `create_agent` + `langgraph dev` backend, `useStream` + react-markdown frontend. |
| `langchain/sandbox` | DeepAgents sandbox coding agent with LangSmith sandbox backend and streaming UI. |
| `deepagents/default` | Local `create_deep_agent` runnable bound to `agentseek-langchain`. |
| `deepagents/research` | Pure DeepAgents research agent with Tavily search and streamed tool/sub-agent UI. |
| `deepagents/content-builder` | DeepAgents content builder with brand memory, skills, subagents, image generation, and streamed UI. |

## Selection

| Need | Start with |
| --- | --- |
| Recommended AgentSeek harness app | `deepagents/default` |
| Lightest harness app without LangChain | `bub/default` |
| Bub app with semantic memory | `bub/contextseek` |
| LangChain app inside AgentSeek runtime | `langchain/default` |
| Pure LangChain app with `langgraph dev` | `langchain/markdown-messages` |
| Remote LangGraph service | `langchain/cli-remote` |
| Deep research workflow | `deepagents/research` |
| Content workflow with memory, skills, and images | `deepagents/content-builder` |

## `agentseek create` forms

| Form | Meaning |
| --- | --- |
| `agentseek create` | Interactive type and template selection. |
| `agentseek create --template` | List all templates. |
| `agentseek create --list-templates` | List all templates. |
| `agentseek create <type> --list-templates` | List templates for a type. |
| `agentseek create <type>` | Use the default template for a type. |
| `agentseek create <type/name>` | Use a specific template. |
| `agentseek create <type> --template <name>` | Use a named template under a type. |
| `agentseek create <spec> --output-dir <path>` | Write the generated project under a selected directory. |
| `agentseek create <git-url>` | Use a remote cookiecutter template. |
| `agentseek create <local-path>` | Use a local cookiecutter template. |

## Template inputs

### `bub/default`

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Project directory name. |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `gateway_port` | Default `agentseek gateway` port. |
| `frontend_port` | Vite dev-server port. |
| `copilotkit_port` | CopilotKit Express runtime port. |

### `bub/contextseek`

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Project directory name. |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `gateway_port` | Default `agentseek gateway` port. |
| `frontend_port` | Vite dev-server port. |
| `copilotkit_port` | CopilotKit Express runtime port. |
| `ctx_server_port` | FastAPI ctx HTTP server port. |
| `contextseek_storage_backend` | ContextSeek storage backend. |
| `contextseek_storage_path` | Local ContextSeek store path input. |
| `contextseek_tenant` | ContextSeek tenant identifier. |

### `langchain/default`

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package and directory name. |
| `author` | Project author. |
| `system_prompt` | System prompt baked into the agent. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `gateway_port` | AG-UI gateway port. |
| `frontend_port` | Vite dev-server port. |
| `copilotkit_port` | CopilotKit Express runtime port. |

### `langchain/cli-remote`

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package and directory name. |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `langgraph_url` | LangGraph Agent Server URL. |
| `assistant_id` | Graph or assistant id. |

### `langchain/markdown-messages`

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package and directory name. |
| `author` | Project author. |
| `system_prompt` | System prompt baked into the agent. |
| `default_model` | Model id passed to `init_chat_model(...)`. |
| `langgraph_port` | `langgraph dev` backend port. |
| `frontend_port` | Vite dev-server port. |

### `langchain/sandbox`

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package and directory name. |
| `author` | Project author. |
| `default_model_provider` | Default `init_chat_model(..., model_provider=...)` provider. |
| `default_model` | Model id for the selected provider. |
| `langgraph_port` | `langgraph dev` backend port. |
| `frontend_port` | Vite dev-server port. |

### `deepagents/default`

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package and directory name. |
| `author` | Project author. |
| `system_prompt` | System prompt baked into the agent. |
| `default_model` | Default `AGENTSEEK_MODEL`. |

### `deepagents/research`

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package and directory name. |
| `author` | Project author. |
| `default_model` | Default `init_chat_model("<provider>:<model>")` id. |
| `tavily_max_results` | Default `tavily_search` result limit. |
| `tavily_topic` | Tavily topic filter. |
| `max_concurrent_research_units` | Max sub-agent tasks queued concurrently. |
| `max_researcher_iterations` | Max search/reflection loops per research unit. |
| `langgraph_port` | `langgraph dev` backend port. |
| `frontend_port` | Vite dev-server port. |

### `deepagents/content-builder`

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package and directory name. |
| `author` | Project author. |
| `default_model_provider` | Default `init_chat_model(..., model_provider=...)` provider. |
| `default_model` | Model id for the selected provider. |
| `google_image_model` | Gemini model for image generation. |
| `tavily_max_results` | Default web search result limit. |
| `tavily_topic` | Tavily topic filter. |
| `langgraph_port` | `langgraph dev` backend port. |
| `frontend_port` | Vite dev-server port. |
