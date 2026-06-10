---
title: agentseek 与 LangChain 的关系
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-06-03
sources:
  - templates/index.json
  - contrib/agentseek-langchain/README.md
  - pyproject.toml
---

# agentseek 与 LangChain 的关系

> **一句话：** AgentSeek **不是 LangChain 的替代品**，也不是又一个智能体框架。
> 它是一个**开放接入任何智能体框架**的数据库原生 harness——内置 Bub，当前
> 版本对 LangChain 的集成最深。它补齐 LangChain 开源生态中目前缺失的三块拼图——
> **服务化的 ship 轴**（agentseek-api）、**上下文语义层**（ContextSeek）、以及
> **Agent 时代的数据底座**（langchain-oceanbase + OceanBase / seekdb）。你的
> LangGraph 代码不用改一行就能跑在 AgentSeek 上——不需要切换框架。

## 背景

LangChain v1 和 DeepAgents 提供了强大的 *build* 基础。但 Agent Engineering 闭环——
build → ship → observe → refine——不只需要一个好的 build 阶段。大量团队停在
"本地 demo 能跑"就上不去了，因为后续阶段需要开源端尚未提供的基础设施：

- **Ship**：一个符合 Agent Protocol 标准的服务，能让 LangGraph / LangChain 应用
  不改代码直接上生产。
- **Observe + Refine**：一层语义化的上下文系统，能跨会话积累知识并可检索——
  不只是每次往 prompt 里临时注入。
- **数据底座**：一个让运行时数据（trace、工具调用、context、checkpoint）从第一天起
  就是数据库里一等公民对象的地方。

LangSmith 为付费客户解决了这三块。AgentSeek 为开源社区解决同样的问题。

## 从 LangChain 开发者视角看架构

```text
┌────────────────────────────────────────────────────┐
│  你的 LangGraph / DeepAgents 应用代码               │  ← 你写这一层
├────────────────────────────────────────────────────┤
│  agentseek-langchain（桥接插件）                    │  ← 零改动接入
├────────────────────────────────────────────────────┤
│  agentseek（harness 运行时）                        │  ← gateway、channel、CLI
│  ── 底层由 Bub 内核驱动                             │
├────────────────────────────────────────────────────┤
│  OceanBase / seekdb / langchain-oceanbase          │  ← 数据底座
└────────────────────────────────────────────────────┘
```

关键点：

- **LangChain 是一等公民。** `agentseek-langchain` 桥接插件把 `create_agent` 和
  `create_deep_agent` 的 runnable 直接连进 harness。六套内置模板中四套使用
  LangChain——它是主要支持的框架。
- **你的代码不需要改。** 你写正常的 LangGraph graph；harness 透明包装，负责
  生产交付、上下文管理和数据持久化。
- **Bub 是实现细节。** harness 运行时构建在
  [Bub](https://github.com/bubbuild/bub)（一个 hook-first turn pipeline +
  插件模型）之上。作为 LangChain 开发者你很少需要直接与 Bub 交互——它是让
  harness 工作的底层管道。想了解内部细节可以看
  [Bub 关系](bub-relationship.zh.md)。

## AgentSeek 为 LangChain 开发者增加了什么

| 组件 | 做什么 | 文档 |
| --- | --- | --- |
| **[agentseek-api](https://github.com/ob-labs/agentseek-api)** | Agent Protocol 服务（`/v1/threads`、`/v1/runs`、streaming、Store API、MCP、A2A）。你的 LangGraph 代码不用改一行就能跑成生产服务。 | [README](https://github.com/ob-labs/agentseek-api#readme) |
| **[ContextSeek](https://github.com/ob-labs/contextseek)** | 语义上下文层——统一 `ContextItem`、L0/L1/L2 渐进式披露、EvolutionEngine、DreamEngine。补齐 LangSmith Context Hub 在开源端的空白。 | [README](https://github.com/ob-labs/contextseek#readme) |
| **[langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase)** | LangGraph checkpoint + store + vectorstore + hybrid search，基于 OceanBase / seekdb / MySQL。运行时数据从第一天起就是可查 SQL。 | [README](https://github.com/oceanbase/langchain-oceanbase#readme) |
| **IM Gateway** | 飞书 / 钉钉 / Slack 渠道适配器。Agent 出现在用户真正待着的地方。 | 内置于模板 |
| **[agentseek](https://github.com/ob-labs/agentseek)** | 生成项目、生命周期管理（`new / dev / build / deploy`）。消灭每次新建 agent 项目时的脚手架税。 | [模板参考](../reference/templates.zh.md) |
| **开发 Skills** | 可安装到你的编程助手（Claude Code、Cursor）的引导指南：`langchain-dev-guide`（踩坑与修复）、`langchain-cn-models`（国内模型接入）。AI 助手在你写代码时自动引用。 | [skills/](https://github.com/ob-labs/agentseek/tree/main/skills) |

每个组件有自己的仓库和文档。本站覆盖的是**套件层面的工作流**——各组件如何协同。
API 层面的细节（接口、配置、高级用法）请跳转上表链接。

## Bub-only 与 LangChain 模板的选择

模板按不同开发者画像设计，让你自然落到对的位置：

| 你的背景 | 推荐起步模板 | 运行时依赖 |
| --- | --- | --- |
| 新手，想要最轻路径 | `bub/default` | 仅 Bub（不含 LangChain） |
| LangChain 入门，想最少代码 | `langchain/markdown-messages` | LangChain + `langgraph dev`（无 agentseek 运行时） |
| LangChain 用户，要交付产品 | `langchain/default` | LangChain + agentseek-langchain + CopilotKit + 飞书 |
| 深度研究场景 | `deepagents/research` | DeepAgents + Tavily（无 agentseek 运行时） |
| LangChain 用户，要 harness 数据层 | `deepagents/default` | DeepAgents + agentseek-langchain |
| 连接远程 graph（agentseek-api 或 LangSmith） | `langchain/cli-remote` | LangChain + LangGraphClientRunnable |

标注"无 agentseek 运行时"的模板生成自包含项目，只需 `langgraph dev` 即可运行。
它们不引入 Bub、gateway 或 tape store——适合先用纯 LangChain 体验，等准备好了
再加 harness 层。当你想接入运行时数据层时，切换到包含 `agentseek-langchain` 的
模板即可。

## 工作原理

### 桥接层：`agentseek-langchain`

`agentseek-langchain` contrib 包
（[contrib/agentseek-langchain/](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-langchain)）
注册了一个 Bub 插件，做三件事：

1. 把 LangChain `Runnable`（来自 `create_agent` 或 `create_deep_agent`）包装成
   Bub turn handler。
2. 把 LangChain 事件（tool calls、tokens、sub-agent 委派）流式传入 Bub channel，
   使 gateway 和前端统一接收。
3. 把 checkpoint 和 store 写入配置的 tape store 后端（本地 SQLite / 生产环境
   OceanBase / seekdb）。

从 agent 作者的角度：你写正常的 LangGraph graph，harness 透明包装。

### agentseek-api 与 Agent Protocol

`agentseek-api`（[github.com/ob-labs/agentseek-api](https://github.com/ob-labs/agentseek-api)）
是一个独立的 FastAPI 服务，实现
[Agent Protocol](https://github.com/langchain-ai/agent-protocol)——与 LangSmith
Agent Server 对外暴露的同一套 HTTP 规范。

你把它指向一个引用了你 graph 的 `langgraph.json`；它处理 threads、runs、
streaming、interrupt/resume、Store API、MCP 路由和 A2A 联邦。你的 graph 代码无需
任何修改。

### ContextSeek 作为 LangChain Middleware 的对等层

ContextSeek（[github.com/ob-labs/contextseek](https://github.com/ob-labs/contextseek)）
本身不是 LangChain middleware——它是一个独立的语义层，通过 HTTP 或 MCP 访问。
实践中它与 LangChain Middleware 配对使用：middleware 在每轮之前调用 ContextSeek
注入相关上下文，在每轮之后写回新知识。`agentseek-contextseek` contrib 包在
harness 内部自动接通这一切。

### 数据底座：langchain-oceanbase

`langchain-oceanbase` v0.5.0（[github.com/oceanbase/langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase)）
提供原生 LangGraph 集成：

- **Checkpoint saver**——长程 graph 的持久执行状态。
- **Store**——跨 thread 的持久记忆（namespace 化键值）。
- **VectorStore + Hybrid Search**——基于 embedding 的检索，融合 BM25。

三者均支持 OceanBase、seekdb（server 或 embedded）和 MySQL（仅 checkpoint + store）。
已经标准化在 MySQL 上的用户无需引入新数据库即可接入 agent 数据层——升级到
OceanBase 或 seekdb 后可获得向量搜索能力。这意味着运行时数据从第一天起就是可查的
SQL——与 LangChain 的 SmithDB 在内部提供的结构性体验相同。

## 为什么是这样

- **开放接入智能体框架，当前版本 LangChain 友好。** AgentSeek 的设计目标是成为
  任何智能体框架的底层 harness。它内置 Bub 作为原生框架，当前版本对 LangChain
  的集成最深——四/六的模板、专用桥接插件、原生 langchain-oceanbase 支持。我们
  欢迎新的智能体框架接入——尤其是利用数据底座和上下文层。Bub 就是一个好例子：
  它正是通过这种模式内置为 AgentSeek 的原生框架。集成路径是编写 contrib 插件把你的
  runnable 桥接进 harness。
- **渐进式采纳。** `langchain/markdown-messages` 和 `deepagents/research` 等模板
  不带任何 agentseek 运行时依赖。开发者可以先用纯 LangChain，等准备好了再加
  harness 层，无需重写。
- **一份数据层。** 无论你从哪个模板起步，一旦接入 harness，运行时数据都流入同一个
  数据库底座。不需要二次采集管道。

## 什么时候用 LangChain + AgentSeek vs. 单独用 LangChain

用 LangChain **配合** agentseek harness，当你：

- 从第一天起就需要持久化的运行时数据（checkpoint、store、vectorstore）。
- 想要 IM 渠道送达（飞书、钉钉），而不想自己写适配器。
- 想要 Agent Engineering 闭环（ship → observe → refine）通过 agentseek-api +
  ContextSeek 开箱即用。
- 想要 harness CLI 管理项目（`new / dev / build / deploy`）。

单独用 LangChain **不加** agentseek harness，当你：

- 正在原型阶段，想要最简依赖树。
- 部署到 LangSmith Deployments 或其他托管 LangGraph 运行时。
- 只需要本地 `langgraph dev`，还没准备好上生产。

两种情况下，模板都能在一分钟内给你一个可运行的起点。

## 相关页面

- 概念解释：[agentseek 是什么](what-agentseek-is.zh.md)、
  [agentseek 与 Bub 的关系](bub-relationship.zh.md)、
  [命令概览](cli-surface.zh.md)
- 参考：[模板参考](../reference/templates.zh.md)、
  [包参考](../reference/packages.zh.md)
- 操作指南：[使用 ContextSeek](../how-to/use-contextseek.zh.md)、
  [安装插件](../how-to/install-a-plugin.zh.md)
- 外部链接：[agentseek-api](https://github.com/ob-labs/agentseek-api)、
  [ContextSeek](https://github.com/ob-labs/contextseek)、
  [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase)、
  [Agent Protocol](https://github.com/langchain-ai/agent-protocol)
