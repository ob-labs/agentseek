---
title: 运行时数据模型
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-06-12
sources:
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
  - pyproject.toml
  - contrib/README.md
---

# 运行时数据模型

AgentSeek 使用一组很小的运行时词汇：turn、channel、tape、skill、MCP 和 plugin。

这些概念说明什么进入 harness，什么改变行为，以及持久数据落在哪里。

```text
user or app
  -> channel
  -> turn
  -> runtime hooks from plugins
  -> model, tools, skills, MCP
  -> tape
```

## Turn

Turn 是一次与 runtime 的交互。它包含输入消息、运行时上下文、model 活动、可选工具调用
和输出响应。

## Channel

Channel 是 turn 进入和离开的表面。CLI chat、gateway、飞书、Telegram 和 AG-UI 都是
channel 示例。

Channel 让同一个应用可以出现在不同开发场景和交付场景中，而不需要重写 agent。

## Tape

Tape 是运行时事实的持久记录。它捕获一次交互及其周围步骤，使这些数据可以被回放、
检查、比较或用于评估。

这就是 AgentSeek 中 database-native 的实际含义：运行时数据不是一次性日志。

## Skill

Skill 是用 Markdown 和可选辅助文件打包的任务知识。它指导 agent，但不添加 runtime hook
或新 channel。

当改动是“agent 应该如何处理某类任务”时，使用 skill。

## MCP

MCP 声明 model 可以调用的外部工具。当工具已经存在于 Python 进程外，并且可以通过 server
配置暴露时，使用 MCP。

## Plugin

Plugin 改变 runtime 行为。Plugins 添加 hook、channel、storage、scheduler、model provider
和工具包。

当 runtime 本身需要新能力时，使用 plugin。

## 为什么要分开

每个概念的维护成本不同。Skill 很轻。MCP entry 是配置。Plugin 影响 runtime。
Tape 是持久底座。

保持这些角色分离，项目更容易运维，也更容易扩展。

## 下一步

- [扩展模型](extension-model.zh.md)
- [文件布局参考](../reference/file-layout.zh.md)
- [包参考](../reference/packages.zh.md)
