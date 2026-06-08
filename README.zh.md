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

> **《Deep Agents 实战》**：基于 AgentSeek 实验的 LangChain / DeepAgents 免费课程。
> [课程网站](https://webup.github.io/deepagents-course) · [源码仓库](https://github.com/webup/deepagents-course)

## 两个入口

两个入口对应不同的任务：

| 目标 | 从这里开始 | 适合场景 |
| --- | --- | --- |
| 从模板创建项目 | `agentseek create` | 你需要一个可运行的应用脚手架。 |
| 运行 AgentSeek 本身 | `agentseek chat` 或 `agentseek gateway` | 你要评估、嵌入或运维 harness runtime。 |

### 创建模板项目

```bash
uvx --from agentseek-cli agentseek create --list-templates
uvx --from agentseek-cli agentseek create langchain/markdown-messages
cd markdown_messages_agent
cp .env.example .env
uv sync
uv run langgraph dev
```

当你想先得到一个生成项目形状时，用这个入口。模板覆盖 LangChain、DeepAgents
和 Bub starter。

### 运行 AgentSeek 本身

```bash
uv tool install agentseek
agentseek chat
```

当你需要直接使用 harness runtime 时，用这个入口：chat loop、gateway、plugins、
MCP，或者作为可嵌入的 Python 包。

安装方式和命令归属详见[选择一个入口](docs/explanation/choosing-an-entry-point.zh.md)。

## 这个仓库包含什么

这个仓库包含创建项目和运行 AgentSeek harness 所需的主要部分。

| 部分 | 职责 |
| --- | --- |
| `agentseek` | Harness runtime 和可嵌入的库。 |
| `agentseek-cli` | 项目创建和生命周期命令。 |
| Templates | 面向常见应用形状的 Cookiecutter starter。 |
| `contrib/` | 面向框架、存储和上下文系统的可选集成。 |

相关项目在独立仓库中维护：

| 项目 | 职责 |
| --- | --- |
| [agentseek-api](https://github.com/ob-labs/agentseek-api) | 面向生产 LangGraph 服务的 Agent Protocol server。 |
| [ContextSeek](https://github.com/ob-labs/contextseek) | 语义记忆、检索、演进、HTTP API、MCP 和 LangChain middleware。 |
| [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) | OceanBase、seekdb 或 MySQL 上的 LangGraph checkpoint、store、向量检索和混合检索。 |

AgentSeek 也构建在 [Bub](https://github.com/bubbuild/bub) 之上；Bub 是 hook-first 的
agent runtime 和 framework。

## 组件如何拼起来

常见流程是：

1. 需要应用脚手架时，先创建项目。
2. 需要 harness runtime 时，运行 AgentSeek 本身。
3. 通过 harness 和存储集成沉淀可持久化的 runtime data。
4. 当 agent 需要跨会话上下文时，接入 ContextSeek 语义记忆。
5. 通过 agentseek-api 把生产 LangGraph 应用服务化。

这样首页只保留起步需要知道的入口，存储、记忆和服务化能力在应用需要时再接入。

## 模板选择

选择“创建模板项目”这个入口之后，再挑和应用形状最匹配的最小模板：

| 应用形状 | 从这里开始 |
| --- | --- |
| 最小 LangChain 应用 | `agentseek create langchain/markdown-messages` |
| 完整 AgentSeek 交付应用 | `agentseek create langchain/default` |
| DeepAgents research 应用 | `agentseek create deepagents/research` |
| 不带 LangChain 的 Bub 应用 | `agentseek create bub/default` |

完整目录见[模板参考](docs/reference/templates.zh.md)。

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
