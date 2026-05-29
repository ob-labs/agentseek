---
title: 模板参考
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

# 模板参考

`agentseek create` 使用的捆绑 Cookiecutter 模板。目录清单位于 `templates/index.json`；
每个模板都是位于 `templates/<framework>/<name>/` 下的一个 cookiecutter project。

## 目录

| Spec | 框架 | 名称 | 描述 |
| --- | --- | --- | --- |
| `bub/default` | `bub` | `default` | 轻量级 Bub agent：`agentseek gateway` + CopilotKit 前端，不使用 LangChain。 |
| `langchain/default` | `langchain` | `default` | 通过 `agentseek-langchain` 接入的 LangChain `create_agent` + CopilotKit middleware。 |
| `langchain/cli-remote` | `langchain` | `cli-remote` | 通过 `LangGraphClientRunnable` 桥接的远程 LangGraph CLI agent。 |
| `deepagents/default` | `deepagents` | `default` | 绑定到 `agentseek-langchain` 的本地 `create_deep_agent` runnable。 |

清单来自 `templates/index.json`。

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

## 另请参阅

- 操作指南：[如何安装插件](../how-to/install-a-plugin.zh.md)
- 教程：[构建你的第一个 harness 应用](../tutorials/02-first-harness-app.zh.md)
- 参考：[CLI 参考](cli.zh.md)
