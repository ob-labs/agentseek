# AgentSeek

中文 | [English](README.md)

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

一个由 [OceanBase](https://www.oceanbase.com/) OSS Team 提供的数据库原生 Agent Harness。

## AgentSeek 是什么

AgentSeek 是一个数据库原生的 Agent Harness，适合那些希望把智能体运行时数据变成一等数据库工作负载的团队。它开放接入任何智能体框架——内置 Bub，当前版本开箱即用地支持 LangChain。

它把数据库视为承载 agent 上下文、执行历史、工具调用、任务、反馈和观测数据的自然位置。这样，同一份运行时数据就可以直接服务于调试、回放、轨迹对比、评估、分析和训练工作流，而不需要复制到多个系统中，也不需要事后重新导入。

**AgentSeek 是一个套件**，由多个可独立使用的组件组成：

| 组件 | 做什么 | 仓库 |
| --- | --- | --- |
| **agentseek-cli** | 生成项目、管理生命周期（`create / run / build / deploy`） | [ob-labs/agentseek](https://github.com/ob-labs/agentseek) |
| **agentseek-api** | Agent Protocol 服务——把你的 LangGraph 零改动送上生产 | [ob-labs/agentseek-api](https://github.com/ob-labs/agentseek-api) |
| **ContextSeek** | 语义上下文层——记忆、检索、演进、渐进式披露。自带 LangChain middleware 和 LangSmith `@traceable` 支持 | [ob-labs/contextseek](https://github.com/ob-labs/contextseek) |
| **langchain-oceanbase** | 数据底座——checkpoint + store + 向量 + hybrid search，基于 OceanBase / seekdb / MySQL | [oceanbase/langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) |

每个组件有自己的仓库和文档。本仓库描述套件层面的工作流；各组件的 API 细节请跳转上表链接。

## 快速开始 — 面向 LangChain 开发者

**该选哪个模板？**

- **刚入门 / 想试试？** → `langchain/markdown-messages`（最小化，5 分钟）
- **已有 graph，要交付产品？** → `langchain/default`（前端 + 飞书 IM + 完整运行时）
- **做深度研究、需要 sub-agent？** → `deepagents/research`（Tavily + 报告生成）
- **graph 跑在远程服务器？** → `langchain/cli-remote`

```bash
# 选一个跑：
uvx --from agentseek-cli agentseek create langchain --template markdown-messages
# 或者: langchain --template default
# 或者: deepagents --template research
```

然后：`cd <项目> && uv sync && uv run langgraph dev`（最小化）或 `uv run agentseek run`（完整交付）。

> **LangSmith tracing 已预配置。** 每个模板都自带 `.env.example`，里面 `LANGSMITH_TRACING=true` 和 `LANGSMITH_API_KEY` 已经写好，填入你的 key 就能在 LangSmith 里立刻看到完整的 run 观测。

**Agent 跑起来之后的下一步：**

- 加持久记忆 → [ContextSeek 文档](https://github.com/ob-labs/contextseek)
- 服务化上生产 → [agentseek-api 文档](https://github.com/ob-labs/agentseek-api)
- 换成持久数据库 → [langchain-oceanbase 文档](https://github.com/oceanbase/langchain-oceanbase)
- 安装开发 Skills 获得引导 → 见下方[开发 Skills](#开发-skills)
- 系统学习 DeepAgents → 见下方[开源课程](#开源课程)

### 面向 OceanBase / seekdb / MySQL 开发者

已经在跑 OceanBase、seekdb 或 MySQL？AgentSeek 把你的数据库变成 AI agent 的数据底座。

```bash
pip install langchain-oceanbase[pyseekdb]   # OceanBase / seekdb
pip install langchain-oceanbase             # MySQL（checkpoint + store）
```

MySQL 用户开箱可用 checkpoint 和 store；向量搜索需要 OceanBase 或 seekdb。完整文档：[langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase)。

### 其他路径

AgentSeek 在 PyPI 上以两个互补的包形式提供，按职责拆分：

- **`agentseek-cli`** —— **项目生命周期 CLI**（`create`、`run`、`build`、`deploy`、`api`、`ctx`、`skills`）。自包含，使用 `uv tool install agentseek-cli` 安装。
- **`agentseek`** —— **harness** 本身。提供运行时 CLI（`chat`、`run`、`gateway`、`install`、`update`、…）以及嵌入到你应用里的库。通过本仓库的 `[tool.uv.sources]` 解析。

**已经在用 [Bub](https://github.com/bubbuild/bub)？** AgentSeek 是 Bub 的发行版，带有开箱即用的默认配置。试试 `agentseek create bub --template default`。详见 [AgentSeek 与 Bub 的关系](docs/explanation/bub-relationship.zh.md)。

完整路径对比见 [选择一个入口](docs/explanation/choosing-an-entry-point.zh.md)。

## 开源课程

**《Deep Agents 实战》**——免费课程，用 LangChain / DeepAgents 构建生产级 AI Agent。后续所有动手实验基于 AgentSeek。

[课程网站](https://webup.github.io/deepagents-course) · [源码仓库](https://github.com/webup/deepagents-site)

课程覆盖：Agent Harness 概念、虚拟文件系统、任务规划、sub-agent、异步委派、长期记忆、Human-in-the-Loop、Skills、沙箱执行、流式前端、生产部署。

## 开发 Skills

可安装到你的 AI 编程助手（Claude Code、Cursor 等）的引导指南：

| Skill | 做什么 |
| --- | --- |
| **langchain-dev-guide** | LangChain / LangGraph 工程踩坑与验证过的修复方案。覆盖 DeepAgents、middleware、streaming、multi-agent 编排。 |
| **langchain-cn-models** | 把国内大模型（DeepSeek、通义 Qwen、智谱 GLM、Moonshot 等）接入 LangChain 的分步食谱。 |

```bash
npx skills add ob-labs/agentseek --all
```

完整说明：[skills/](skills/)

## 接入你的智能体框架

AgentSeek 的设计目标是成为任何智能体框架的底层 harness。如果你正在构建新框架，或者维护一个需要持久数据层和语义上下文的框架——欢迎接入。Bub 就是一个好例子：它正是通过这种模式内置为 AgentSeek 的原生框架。AgentSeek 提供数据底座（OceanBase / seekdb / MySQL）、语义上下文层（ContextSeek）和生产服务化（agentseek-api），让你不用自己造这些。

集成模式和 `agentseek-langchain` 一样——编写 contrib 插件把你的 runnable 桥接进 harness。参见[扩展模型](docs/explanation/extension-model.zh.md)和[编写 contrib 插件](docs/how-to/author-a-contrib-plugin.zh.md)。欢迎往 `contrib/` 提 PR。

## 模板

模板是一个**持续增长的集合**——LangChain 和 Bub 两个系列都在不断添加和打磨。欢迎提交 PR。

| 模板 | 描述 |
| --- | --- |
| `langchain/markdown-messages` | 纯 LangChain 聊天机器人，`langgraph dev` 后端，markdown 渲染前端。 |
| `langchain/default` | LangChain + CopilotKit 前端 + 飞书 IM Gateway + 完整 agentseek 运行时。 |
| `langchain/cli-remote` | 通过 `LangGraphClientRunnable` 桥接远程 LangGraph 服务。 |
| `deepagents/research` | DeepAgents 研究 Agent，内置 Tavily 搜索和流式报告 UI。 |
| `deepagents/default` | `create_deep_agent` 绑定到 `agentseek-langchain`。 |
| `bub/default` | 轻量 Bub agent + CopilotKit 前端，不含 LangChain。 |

详见[模板参考](docs/reference/templates.zh.md)。

## Docker Compose

```bash
cp .env.example .env
make compose-up
```

详见 [使用 Docker Compose 运行](docs/how-to/run-with-docker-compose.zh.md)。

## 文档

- [首页](docs/index.zh.md) — 套件总览，多角色快速开始
- [教程](docs/tutorials/index.zh.md) — 快速演示、第一个应用、skills 与 MCP
- [操作指南](docs/how-to/index.zh.md) — 任务式食谱
- [概念解释](docs/explanation/index.zh.md) — LangChain 关系、Bub 关系、运行时数据模型
- [参考](docs/reference/index.zh.md) — 环境变量、CLI、包、模板、Docker

更多包文档：

- [agentseek-langchain](contrib/agentseek-langchain/README.md)
- [agentseek-tapestore-oceanbase](contrib/agentseek-tapestore-oceanbase/README.md)
- [agentseek-contextseek](contrib/agentseek-contextseek/README.md)
- [agentseek-schedule-sqlalchemy](contrib/agentseek-schedule-sqlalchemy/README.md)

## 工作原理

- **组件套件** — agentseek-cli、agentseek-api、ContextSeek、langchain-oceanbase。可组合使用，也可独立使用。
- **Bub 作为运行时内核** — [Bub](https://github.com/bubbuild/bub) 提供 hook-first turn pipeline、tape store、skills、plugins 和 channel model。AgentSeek 把 Bub 作为库依赖消费。
- **LangChain 桥接** — `agentseek-langchain` contrib 插件把 LangGraph runnable 透明接入 harness turn pipeline。
- **`.agentseek` 运行时 home** — 工作区本地的配置、插件沙箱和运行时状态。
- **环境变量别名** — `AGENTSEEK_*` 为同名 `BUB_*` 提供回退值。
- **开放式 authoring model** — `AGENTS.md`、项目级 skills、MCP 配置都是一等扩展入口。

如果你想从本地开发一路走到更大的部署场景，我们推荐 [OceanBase seekdb](https://github.com/oceanbase/seekdb) 和 OceanBase。

## 开发

```bash
make install
make check
make test
make docs-test
```

## License

[Apache-2.0](LICENSE)
