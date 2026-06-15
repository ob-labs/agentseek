---
title: LangChain 关系
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-06-12
sources:
  - templates/index.json
  - contrib/agentseek-langchain/README.md
  - pyproject.toml
---

# LangChain 关系

AgentSeek 不替代 LangChain。它是开放给 agent framework 的 database-native
harness，而当前最深入的集成面向 LangChain 和 DeepAgents。

LangChain 仍然负责构建 graph、agent、tool 和 model call。AgentSeek 放在应用周围，
处理原型跑通之后才会集中出现的问题：服务交付、语义 context、runtime 扩展和持久
运行时数据。

## 为什么适合放在一起

LangChain 强在 build 层。AgentSeek 关注围绕它的 agent engineering loop：

- **Ship**：gateway、channel、项目命令和生产服务路径。
- **Observe and refine**：可回放、可检查、可评估的运行时数据。
- **Remember**：通过 ContextSeek 和相关扩展，让语义 context 跨 turn 和 session 积累。
- **Store**：用 OceanBase、seekdb 或其他受支持后端保存 checkpoint、工具调用、trace、
  memory 和反馈等 agent-era data。

桥接包 `agentseek-langchain` 将 LangChain runnable 连接到 AgentSeek runtime。
你的 graph 仍然是 LangChain graph；harness 处理外围生命周期。

```text
LangGraph or DeepAgents application
  -> agentseek-langchain bridge
  -> AgentSeek harness on the Bub runtime
  -> tape store, ContextSeek, gateway, channels, and plugins
```

## AgentSeek 增加什么

| 层 | 增加的能力 |
| --- | --- |
| Service layer | `agentseek-api`、gateway 交付、生成式前端 / runtime 项目和部署产物。 |
| Semantic context | 通过 HTTP、MCP 或 contrib package 接入 ContextSeek。 |
| Data substrate | Tape store、checkpoint、memory、向量或混合检索，以及 OceanBase / seekdb 集成。 |
| Extension surface | 面向 channel、model provider、MCP、store、scheduler 和观测能力的 Bub-compatible plugin。 |

关键点是这些层可以叠加。LangChain graph 不需要变成 Bub 应用，也可以获得 harness 能力。

## 模板路径

AgentSeek 仓库同时维护纯 LangChain 模板和带 harness 的模板。这样可以渐进采用：

- 当你想要最小依赖树，或计划直接使用 `langgraph dev` 时，从纯 LangChain 模板开始。
- 当你从第一天就需要 channel、项目生命周期命令或运行时数据时，从带 harness 的模板开始。
- 当原型需要服务交付、memory、评估或 database-backed runtime layer 时，再加入 AgentSeek。

[模板参考](../reference/templates.zh.md) 列出准确的模板清单。

## AgentSeek 何时有价值

当应用需要以下能力之一时，将 LangChain 与 AgentSeek 配合使用：

- 可重复本地运行循环的生成项目；
- gateway 或聊天 channel 交付；
- 基于 plugin 的存储、context、MCP、调度或可观测性；
- 从本地开发到容器构建和部署清单的路径；
- 可查询、可复用的运行时数据。

当小型本地原型或托管 LangGraph runtime 已经覆盖所需生命周期时，可以单独使用
LangChain。

## 下一步

- [模板参考](../reference/templates.zh.md)
- [运行时数据模型](runtime-data-model.zh.md)
- [扩展模型](extension-model.zh.md)
