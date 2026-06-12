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

AgentSeek 不替代 LangChain。它为 LangChain 应用提供生命周期、channel、扩展和
持久运行时数据的 harness。

LangChain 仍然负责构建 graph、agent、tool 和 model call。当你需要项目脚手架、
gateway 交付、基于 plugin 的扩展和 database-native 运行层时，AgentSeek 位于应用
周围。

## 为什么适合放在一起

LangChain 强在应用层。AgentSeek 关注应用外侧的操作层：

- 项目如何创建和运行；
- 消息如何通过 CLI、gateway 或聊天 channel 进入；
- 运行时数据如何被捕获，用于回放和评估；
- 存储、context、MCP 和 framework bridge 如何安装。

桥接包 `agentseek-langchain` 将 LangChain runnable 连接到 AgentSeek runtime。
你的 graph 仍然是 LangChain graph；harness 处理外围生命周期。

## 模板路径

AgentSeek 同时提供纯 LangChain 模板和带 harness 的模板。这样可以渐进采用：

- 当你想要最小依赖树时，从纯 LangChain 模板开始。
- 当你从第一天就需要 channel、项目生命周期命令或运行时数据时，从带 harness 的模板开始。
- 当原型需要成为可运维服务时，再加入 AgentSeek。

[模板参考](../reference/templates.zh.md) 列出准确的模板清单。

## AgentSeek 何时有价值

当应用需要以下能力之一时，将 LangChain 与 AgentSeek 配合使用：

- 可重复本地运行循环的生成项目；
- gateway 或聊天 channel 交付；
- 基于 plugin 的存储、context、MCP 或可观测性；
- 从本地开发到容器构建和部署清单的路径；
- 可查询、可复用的运行时数据。

当小型本地原型或托管 LangGraph runtime 已经覆盖所需生命周期时，可以单独使用
LangChain。

## 下一步

- [模板参考](../reference/templates.zh.md)
- [运行时数据模型](runtime-data-model.zh.md)
- [扩展模型](extension-model.zh.md)
