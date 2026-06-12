---
title: AgentSeek 是什么
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-06-12
sources:
  - README.md
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
---

# AgentSeek 是什么

AgentSeek 是面向 agent 应用的 database-native harness。

它为项目生命周期提供一个统一的操作表面：创建 starter project、本地运行、
接入运行时扩展、构建镜像，以及通过 CLI、gateway 或聊天集成运行 channel。

## 它解决的问题

Agent 项目通常从代码和 prompt 开始。真正的运行时事实会随后出现：消息、工具调用、
上下文、trace、checkpoint、反馈和评估数据。

如果这些事实散落在不同系统里，回放和运维会变困难。AgentSeek 采用相反的模型：
运行时数据从一开始就应该持久、可查询。

## 模型

AgentSeek 分开处理三类关注点：

- **应用代码** 留在你生成或嵌入的项目里。
- **运行时行为** 通过 Bub 流动：turn、channel、hook、plugin 和 skill。
- **运行时数据** 通过 tape 模型进入持久存储。

因此 AgentSeek 是 harness，不是 agent framework 的替代品。LangChain、DeepAgents、
Bub-native 或自定义应用都可以沿用自己的应用结构，同时进入同一套生命周期。

## AgentSeek 负责什么

AgentSeek 负责让 harness 能在项目中可用的 distribution-level 选择：

- 单一 `agentseek` 命令；
- `.agentseek/` 下的 workspace-local 运行时默认值；
- 项目模板；
- plugin 和 skill 入口；
- Docker 与 gateway 入口；
- 面向 Bub runtime 的 `AGENTSEEK_*` 环境变量别名。

## 它不负责什么

AgentSeek 不强制某个 agent framework、数据库后端、前端或托管服务。这些选择属于你的
应用和你安装的扩展。

## 下一步

- [运行时数据模型](runtime-data-model.zh.md)
- [扩展模型](extension-model.zh.md)
- [Bub 关系](bub-relationship.zh.md)
- [LangChain 关系](langchain-relationship.zh.md)
