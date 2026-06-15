---
title: 模板参考
type: reference
audience: [A2]
runs: no
verified_on: 2026-06-12
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

# 模板参考

## 清单

| Spec | 说明 |
| --- | --- |
| `bub/default` | 轻量 Bub agent：`agentseek gateway` + CopilotKit 前端，不使用 LangChain。 |
| `bub/contextseek` | 带 ContextSeek 语义记忆层和 ctx HTTP API 的 Bub agent。 |
| `langchain/default` | 通过 `agentseek-langchain` 接入的 LangChain `create_agent` + CopilotKit middleware。 |
| `langchain/cli-remote` | 通过 `LangGraphClientRunnable` 桥接的远程 LangGraph CLI agent。 |
| `langchain/markdown-messages` | 纯 LangChain `create_agent` + `langgraph dev` 后端，`useStream` + react-markdown 前端。 |
| `langchain/sandbox` | 带 LangSmith sandbox 后端和 streaming UI 的 DeepAgents coding agent。 |
| `deepagents/default` | 绑定到 `agentseek-langchain` 的本地 `create_deep_agent` runnable。 |
| `deepagents/research` | 带 Tavily 搜索和 streamed tool/sub-agent UI 的纯 DeepAgents research agent。 |
| `deepagents/content-builder` | 带品牌记忆、skills、subagents、图片生成和 streamed UI 的 DeepAgents content builder。 |

## 选择入口

| 需求 | 起点 |
| --- | --- |
| 推荐的 AgentSeek harness app | `deepagents/default` |
| 不带 LangChain 的最轻 harness app | `bub/default` |
| 带语义 memory 的 Bub app | `bub/contextseek` |
| 进入 AgentSeek runtime 的 LangChain app | `langchain/default` |
| 使用 `langgraph dev` 的纯 LangChain app | `langchain/markdown-messages` |
| 远程 LangGraph service | `langchain/cli-remote` |
| Deep research workflow | `deepagents/research` |
| 带 memory、skills 和图片生成的 content workflow | `deepagents/content-builder` |

## `agentseek create` 形态

| 形式 | 含义 |
| --- | --- |
| `agentseek create` | 交互式选择 type 和 template。 |
| `agentseek create --template` | 列出全部模板。 |
| `agentseek create --list-templates` | 列出全部模板。 |
| `agentseek create <type> --list-templates` | 列出指定 type 下的模板。 |
| `agentseek create <type>` | 使用某个 type 的默认模板。 |
| `agentseek create <type/name>` | 使用指定模板。 |
| `agentseek create <type> --template <name>` | 使用某个 type 下的命名模板。 |
| `agentseek create <git-url>` | 使用远程 cookiecutter 模板。 |
| `agentseek create <local-path>` | 使用本地 cookiecutter 模板。 |

## 模板输入

### `bub/default`

| 变量 | 说明 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | 项目目录名。 |
| `author` | 项目作者。 |
| `default_model` | 默认 `AGENTSEEK_MODEL`。 |
| `gateway_port` | 默认 `agentseek gateway` 端口。 |
| `frontend_port` | Vite dev-server 端口。 |
| `copilotkit_port` | CopilotKit Express runtime 端口。 |

### `bub/contextseek`

| 变量 | 说明 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | 项目目录名。 |
| `author` | 项目作者。 |
| `default_model` | 默认 `AGENTSEEK_MODEL`。 |
| `gateway_port` | 默认 `agentseek gateway` 端口。 |
| `frontend_port` | Vite dev-server 端口。 |
| `copilotkit_port` | CopilotKit Express runtime 端口。 |
| `ctx_server_port` | FastAPI ctx HTTP server 端口。 |
| `contextseek_storage_backend` | ContextSeek 存储后端。 |
| `contextseek_storage_path` | 本地 ContextSeek store path 输入。 |
| `contextseek_tenant` | ContextSeek tenant 标识。 |

### `langchain/default`

| 变量 | 说明 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python package 和目录名。 |
| `author` | 项目作者。 |
| `system_prompt` | 写入 agent 的 system prompt。 |
| `default_model` | 默认 `AGENTSEEK_MODEL`。 |
| `gateway_port` | AG-UI gateway 端口。 |
| `frontend_port` | Vite dev-server 端口。 |
| `copilotkit_port` | CopilotKit Express runtime 端口。 |

### `langchain/cli-remote`

| 变量 | 说明 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python package 和目录名。 |
| `author` | 项目作者。 |
| `default_model` | 默认 `AGENTSEEK_MODEL`。 |
| `langgraph_url` | LangGraph Agent Server URL。 |
| `assistant_id` | Graph 或 assistant id。 |

### `langchain/markdown-messages`

| 变量 | 说明 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python package 和目录名。 |
| `author` | 项目作者。 |
| `system_prompt` | 写入 agent 的 system prompt。 |
| `default_model` | 传给 `init_chat_model(...)` 的模型 id。 |
| `langgraph_port` | `langgraph dev` 后端端口。 |
| `frontend_port` | Vite dev-server 端口。 |

### `langchain/sandbox`

| 变量 | 说明 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python package 和目录名。 |
| `author` | 项目作者。 |
| `default_model_provider` | 默认 `init_chat_model(..., model_provider=...)` provider。 |
| `default_model` | 所选 provider 的模型 id。 |
| `langgraph_port` | `langgraph dev` 后端端口。 |
| `frontend_port` | Vite dev-server 端口。 |

### `deepagents/default`

| 变量 | 说明 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python package 和目录名。 |
| `author` | 项目作者。 |
| `system_prompt` | 写入 agent 的 system prompt。 |
| `default_model` | 默认 `AGENTSEEK_MODEL`。 |

### `deepagents/research`

| 变量 | 说明 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python package 和目录名。 |
| `author` | 项目作者。 |
| `default_model` | 默认 `init_chat_model("<provider>:<model>")` id。 |
| `tavily_max_results` | `tavily_search` 默认结果数量上限。 |
| `tavily_topic` | Tavily topic filter。 |
| `max_concurrent_research_units` | 同时排队的最大 sub-agent 任务数。 |
| `max_researcher_iterations` | 每个 research unit 的最大搜索 / 反思循环数。 |
| `langgraph_port` | `langgraph dev` 后端端口。 |
| `frontend_port` | Vite dev-server 端口。 |

### `deepagents/content-builder`

| 变量 | 说明 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python package 和目录名。 |
| `author` | 项目作者。 |
| `default_model_provider` | 默认 `init_chat_model(..., model_provider=...)` provider。 |
| `default_model` | 所选 provider 的模型 id。 |
| `google_image_model` | 图片生成用 Gemini model。 |
| `tavily_max_results` | Web search 默认结果数量上限。 |
| `tavily_topic` | Tavily topic filter。 |
| `langgraph_port` | `langgraph dev` 后端端口。 |
| `frontend_port` | Vite dev-server 端口。 |
