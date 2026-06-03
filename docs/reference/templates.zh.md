---
title: 模板参考
type: reference
audience: [A2]
runs: no
verified_on: 2026-06-03
sources:
  - templates/index.json
  - templates/bub/default/README.md
  - templates/langchain/default/README.md
  - templates/langchain/cli-remote/README.md
  - templates/langchain/markdown-messages/README.md
  - templates/deepagents/default/README.md
  - templates/deepagents/research/README.md
---

# 模板参考

`agentseek create` 使用的捆绑 Cookiecutter 模板。目录清单位于 `templates/index.json`；
每个模板都是位于 `templates/<framework>/<name>/` 下的一个 cookiecutter project。

> **这是一个持续增长的集合。** 我们在不断添加新模板和打磨已有模板——LangChain 和
> Bub 两个系列都在持续更新。关注
> [templates/ 目录](https://github.com/ob-labs/agentseek/tree/main/templates)
> 获取最新动态，也欢迎提交新模板的 PR。

## 目录

| Spec | 框架 | 名称 | 描述 |
| --- | --- | --- | --- |
| `bub/default` | `bub` | `default` | 轻量级 Bub agent：`agentseek gateway` + CopilotKit 前端，不使用 LangChain。 |
| `langchain/default` | `langchain` | `default` | 通过 `agentseek-langchain` 接入的 LangChain `create_agent` + CopilotKit middleware。 |
| `langchain/cli-remote` | `langchain` | `cli-remote` | 通过 `LangGraphClientRunnable` 桥接的远程 LangGraph CLI agent。 |
| `langchain/markdown-messages` | `langchain` | `markdown-messages` | 纯 LangChain `create_agent` + `langgraph dev` 后端，`useStream` + react-markdown 前端。无 agentseek 运行时依赖。 |
| `deepagents/default` | `deepagents` | `default` | 绑定到 `agentseek-langchain` 的本地 `create_deep_agent` runnable。 |
| `deepagents/research` | `deepagents` | `research` | 纯 DeepAgents 研究 Agent，内置 Tavily 搜索和流式 tool/sub-agent UI。 |

清单来自 `templates/index.json`。

## 选择模板

不同模板适合不同的开发者画像和使用场景：

| 如果你是…… | 推荐模板 | 原因 |
| --- | --- | --- |
| 刚接触 LangChain 和 Agent | `langchain/markdown-messages` | 依赖最少，5 分钟从零跑到一个能用的聊天机器人。之后按需加功能。 |
| LangChain 用户，想完整交付产品 | `langchain/default` | 自带 CopilotKit 前端 + 飞书 IM Gateway + agentseek 运行时——交付给利益相关方所需的一切。 |
| 想做深度研究 Agent | `deepagents/research` | 预装 Tavily 搜索、sub-agent 委派、流式报告 UI——对标 DeepAgents 上游的 research 模式。 |
| 要连接远程 LangGraph 服务 | `langchain/cli-remote` | 通过 `LangGraphClientRunnable` 桥接 `langgraph dev`；适合 graph 运行在别处（agentseek-api、LangSmith 等）的场景。 |
| 想要最轻的 harness 路径（不带 LangChain） | `bub/default` | 纯 Bub 内核 + CopilotKit 前端；依赖树里没有 LangChain。 |
| 要把 LangChain 和 agentseek 运行时打通 | `deepagents/default` | `create_deep_agent` 绑定到 `agentseek-langchain`——harness 数据层和 DeepAgents 编排一起拿到。 |

## `agentseek create` 参数形态

| 形式 | 含义 |
| --- | --- |
| `agentseek create bub` | 该框架的默认模板（`bub/default`）。 |
| `agentseek create langchain/cli-remote` | 指定的 `type/name` spec。 |
| `agentseek create langchain --template cli-remote` | 等价的命名模板形式。 |
| `agentseek create <git-url>` | 拉取远程 cookiecutter；可与 `--checkout` 组合。 |
| `agentseek create <local-path>` | 使用本地 cookiecutter 目录。 |
| `agentseek create <type> --list-templates` | 列出该类型的模板并退出。 |

完整的标志表参见 [CLI 参考](cli.zh.md)。

## 每个模板的输入

### `bub/default`

镜像 `examples/ag-ui`。生成一个 AG-UI gateway 以及基于 CopilotKit 的前端。

| 变量 | 描述 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Project / 目录名。 |
| `author` | 项目作者。 |
| `default_model` | 默认 `AGENTSEEK_MODEL`。 |
| `gateway_port` | `agentseek gateway` 的默认端口。 |
| `frontend_port` | 前端 Vite dev server 端口。 |

### `langchain/default`

镜像 `examples/ag_ui_langchain`。生成一个 `create_agent` 项目，通过
`agentseek-langchain` 绑定到 agentseek，并附带 CopilotKit middleware。

| 变量 | 描述 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python 包 / 目录名。 |
| `author` | 项目作者。 |
| `system_prompt` | 烘焙到 agent 中的 system prompt。 |
| `default_model` | 默认 `AGENTSEEK_MODEL`。 |

### `langchain/cli-remote`

镜像 `examples/langchain_cli_remote_agent`。通过 `langgraph dev` 运行 graph，
并通过 `LangGraphClientRunnable` 进行桥接。

| 变量 | 描述 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python 包 / 目录名。 |
| `author` | 项目作者。 |
| `default_model` | 默认 `AGENTSEEK_MODEL`。 |
| `langgraph_url` | 默认 LangGraph Agent Server URL。 |
| `assistant_id` | Graph / assistant id（与 `langgraph.json` 匹配）。 |

### `langchain/markdown-messages`

纯 LangChain 模板，不依赖 agentseek 运行时。生成一个由 `langgraph dev` 提供服务的
`create_agent` 后端，以及通过 `useStream` 流式传输并以 markdown 渲染消息的
Vite + React 前端。

| 变量 | 描述 |
| --- | --- |
| `project_name` | 人类可读的项目名。默认 "Markdown Messages Agent"。 |
| `project_slug` | Python 包 / 目录名（自动推导）。 |
| `author` | 项目作者。 |
| `system_prompt` | 烘焙到 agent 中的 system prompt。 |
| `default_model` | 传给 `init_chat_model(...)` 的模型 id。 |
| `langgraph_port` | `langgraph dev` 的后端端口。默认 `2024`。 |
| `frontend_port` | 前端 dev-server 端口。默认 `5174`。 |

### `deepagents/default`

镜像 `examples/langchain_deepagents`。通过 `agentseek-langchain` 绑定到 agentseek 的
本地 `create_deep_agent(...)` runnable。

| 变量 | 描述 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python 包 / 目录名（自动推导）。 |
| `author` | 项目作者。 |
| `system_prompt` | 烘焙到 agent 中的 system prompt。 |
| `default_model` | 默认 `AGENTSEEK_MODEL`。 |

### `deepagents/research`

纯 DeepAgents 研究模板。搭建一个带有 Tavily 搜索、sub-agent 任务委派的
`create_deep_agent(...)` 项目，以及展示工具调用和最终 markdown 报告的流式前端。

| 变量 | 描述 |
| --- | --- |
| `project_name` | 人类可读的项目名。 |
| `project_slug` | Python 包 / 目录名（自动推导）。 |
| `author` | 项目作者。 |
| `default_model` | 默认 `init_chat_model("<provider>:<model>")` id。 |
| `tavily_max_results` | `tavily_search` 默认结果数量上限。 |
| `tavily_topic` | Tavily 主题过滤（`general`、`news` 或 `finance`）。 |
| `max_concurrent_research_units` | 编排器同时排队的最大 sub-agent 任务数。 |
| `max_researcher_iterations` | 每个 research unit 的最大搜索/反思循环数。 |
| `langgraph_port` | `langgraph dev` 的默认后端端口。 |
| `frontend_port` | 默认 Vite dev-server 端口。 |

## 生成项目之后——下一步

Agent 跑起来之后，按需接入套件的各组件：

| 下一步 | 组件 | 文档 |
| --- | --- | --- |
| 加持久记忆和语义检索 | ContextSeek | [github.com/ob-labs/contextseek](https://github.com/ob-labs/contextseek) |
| 把 graph 服务化上生产 | agentseek-api | [github.com/ob-labs/agentseek-api](https://github.com/ob-labs/agentseek-api) |
| 换成 OceanBase / seekdb 做持久存储 | langchain-oceanbase | [github.com/oceanbase/langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) |
| 在 harness 里接通 ContextSeek | agentseek-contextseek | [使用 ContextSeek](../how-to/use-contextseek.zh.md) |
| 接飞书 / 钉钉 / Slack | IM Gateway | [运行 gateway](../how-to/run-gateway.zh.md) |

## 另请参阅

- 操作指南：[如何安装插件](../how-to/install-a-plugin.zh.md)
- 教程：[构建你的第一个 harness 应用](../tutorials/02-first-harness-app.zh.md)
- 参考：[CLI 参考](cli.zh.md)
