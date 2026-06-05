# AgentSeek

中文 | [English](README.md)

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

由 [OceanBase](https://www.oceanbase.com/) OSS Team 提供的数据库原生 Agent Harness。

AgentSeek 帮团队把 agent 运行时数据变成数据库工作负载：turn、context、工具调用、
任务、反馈、checkpoint、memory 和观测数据都保持可查询，而不是散落在日志和外围系统里。

它面向这样的场景：你已经有 [LangChain](https://github.com/langchain-ai/langchain)、
[DeepAgents](https://docs.langchain.com/oss/deepagents) 或
[Bub](https://github.com/bubbuild/bub) 原型，接下来需要把它整理成边界清晰、
可维护、可运行、可存储、可观测、可服务化的 agent 应用。

## 两个入口

不要先按框架选路，先按你要做的事情选入口：

| 事情 | 包 | 命令面 |
| --- | --- | --- |
| 从模板创建项目 | `agentseek-cli` | `agentseek create`，以及 `run`、`build`、`deploy` 等项目生命周期命令。 |
| 运行 AgentSeek 本身 | `agentseek` | `chat`、`gateway`、`install`、`mcp`、`onboard` 等 harness runtime 命令。 |

### 创建模板项目

```bash
uvx --from agentseek-cli agentseek create --template
uvx --from agentseek-cli agentseek create langchain/markdown-messages
cd markdown_messages_agent
cp .env.example .env
uv sync
uv run langgraph dev
```

当你想先得到一个生成项目形状时，用这个入口。模板可以从 LangChain、DeepAgents
或 Bub 开始，不要求你先 clone 本仓库。

### 运行 AgentSeek 本身

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek chat
```

当你需要直接使用 harness runtime 时，用这个入口：chat loop、gateway、plugins、
MCP，或者作为可嵌入的 Python 包。如果只需要发布版 runtime 包，可以用
`pip install agentseek` 安装。

在本仓库内，或在 `agentseek create` 生成后又执行过 sync 的项目内，单个
`agentseek` 命令可能同时暴露两边的能力。包边界详见
[选择一个入口](docs/explanation/choosing-an-entry-point.zh.md)。

## 这个仓库负责什么

AgentSeek 是一个套件。这个仓库负责 harness 发行版、生命周期 CLI、模板、文档和 contrib
集成。

| 部分 | 职责 | 何时使用 |
| --- | --- | --- |
| `agentseek` | Harness runtime 和库 | 嵌入或运行 turn pipeline、gateway、skills、plugins 和 runtime state。 |
| `agentseek-cli` | 项目生命周期 CLI | 创建、运行、构建、部署和检查生成项目。 |
| Templates | Cookiecutter 项目模板 | 快速得到可运行的 LangChain、DeepAgents 或 Bub 项目形状。 |
| `contrib/` | 集成包 | 把框架或存储后端接入 harness。 |

相关项目在独立仓库中维护：

| 项目 | 职责 |
| --- | --- |
| [agentseek-api](https://github.com/ob-labs/agentseek-api) | 面向生产 LangGraph 服务的 Agent Protocol server。 |
| [ContextSeek](https://github.com/ob-labs/contextseek) | 语义记忆、检索、演进、HTTP API、MCP 和 LangChain middleware。 |
| [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) | OceanBase、seekdb 或 MySQL 上的 LangGraph checkpoint、store、向量检索和混合检索。 |

AgentSeek 也构建在 [Bub](https://github.com/bubbuild/bub) 之上；Bub 是 hook-first 的
agent runtime 和 framework。

## 组件如何拼起来

两个入口在 runtime 边界汇合：

1. 需要生成项目时，用 `agentseek-cli`。
2. 需要运行 harness 本身时，用 `agentseek`。
3. 通过 harness 和存储集成沉淀可持久化的 runtime data。
4. 当 agent 需要跨会话上下文时，接入 ContextSeek 语义记忆。
5. 通过 agentseek-api 把生产 LangGraph 应用服务化。

这个拆分让项目边界更清楚：本仓库提供 harness、CLI、模板和集成；相邻仓库分别负责生产服务、
语义上下文和数据库侧的 LangChain 存储能力。

## 模板选择

选择“创建模板项目”这个入口之后，再挑和应用形状最匹配的最小模板：

| 应用形状 | 从这里开始 |
| --- | --- |
| 最小 LangChain 应用 | `agentseek create langchain/markdown-messages` |
| 完整 AgentSeek 交付应用 | `agentseek create langchain/default` |
| DeepAgents research 应用 | `agentseek create deepagents/research` |
| 不带 LangChain 的 Bub 应用 | `agentseek create bub/default` |

完整目录见[模板参考](docs/reference/templates.zh.md)，全部命令参数见
[CLI 参考](docs/reference/cli.zh.md)。

## 文档

- [文档首页](docs/index.zh.md)
- [教程](docs/tutorials/index.zh.md)
- [操作指南](docs/how-to/index.zh.md)
- [概念解释](docs/explanation/index.zh.md)
- [参考](docs/reference/index.zh.md)

本仓库中的常用包文档：

- [agentseek-langchain](contrib/agentseek-langchain/README.md)
- [agentseek-tapestore-oceanbase](contrib/agentseek-tapestore-oceanbase/README.md)
- [agentseek-contextseek](contrib/agentseek-contextseek/README.md)
- [agentseek-schedule-sqlalchemy](contrib/agentseek-schedule-sqlalchemy/README.md)

## 开发

```bash
make install
make check
make test
make docs-test
```

## License

[Apache-2.0](LICENSE)
