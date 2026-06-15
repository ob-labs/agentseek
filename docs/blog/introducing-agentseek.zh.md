---
title: 认识 AgentSeek
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-06-15
sources:
  - README.zh.md
  - docs/explanation/what-agentseek-is.zh.md
  - docs/explanation/runtime-data-model.zh.md
  - docs/explanation/bub-relationship.zh.md
  - docs/explanation/langchain-relationship.zh.md
---

# 认识 AgentSeek

**2026-06-15**

AgentSeek 是面向 agent 应用的 database-native harness。它帮团队把运行时数据变成
数据库工作负载：turn、context、工具调用、任务、反馈、checkpoint、memory 和观测数据
都保持可查询，而不是散落在日志和外围系统里。

这个定位就是项目本身。AgentSeek 不是另一个 agent framework。它是围绕 framework
的一层：项目如何创建、turn 如何通过 channel 进入、哪些扩展参与运行、运行时事实最终
落在哪里。

## 从 bubseek 到 AgentSeek

最早的工作叫 `bubseek`，探索的是 seekdb 上的 insight 风格 agent。后来我们发现，真正
有价值的部分比单个垂直 agent 更通用：任何严肃的 agent 项目都需要一个持久运行时底座。

AgentSeek 把这个底座保持得很小。Bub 提供 runtime kernel：turn、channel、hook、
tape、skill 和 plugin。AgentSeek 在它之上提供项目默认值、模板、contrib integrations
和公开的 `agentseek` 命令。

## 为什么是 database-native

Agent run 会先产生有价值的事实，然后才产生稳定产品。消息、工具调用、trace、
checkpoint、反馈和 memory，之后都会被调试、回放、评估和训练继续使用。

如果每个消费方都维护自己的日志或旁路管道，项目会越来越难运维。AgentSeek 选择把
tape 当作持久运行时事实流。项目可以从本地轻量存储开始；当需要更强的后端时，同一种
数据形状可以进入 OceanBase、seekdb 或其他受支持的 store。

Database-native 不等于 database-coupled。Harness 定义运行时形状和扩展点；存储后端
仍然是部署选择。

## 为什么是 harness

LangChain、DeepAgents 这样的 framework 是开发者构建 graph、agent、tool 和 model call
的地方。AgentSeek 放在应用周围，处理服务交付、语义 context、runtime 扩展和可查询的
运行时数据。

这也是为什么推荐模板是 `deepagents/default`：它把 DeepAgents runnable 放进
AgentSeek harness，同时应用代码仍然保持清楚。

## 从哪里开始

- 从 `deepagents/default` 构建推荐应用：[模板参考](../reference/templates.zh.md)。
- 理解数据模型：[运行时数据模型](../explanation/runtime-data-model.zh.md)。
- 了解 LangChain 和 DeepAgents 如何接入：[LangChain 关系](../explanation/langchain-relationship.zh.md)。
- 浏览集成：[Hub](../hub.zh.md)。
