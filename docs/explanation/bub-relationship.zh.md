---
title: Bub 关系
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-06-12
sources:
  - src/agentseek/env.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/__main__.py
  - pyproject.toml
  - entrypoint.sh
---

# Bub 关系

AgentSeek 是构建在 Bub 之上的 distribution，不是 Bub 的 fork。

Bub 提供 runtime kernel：turn、channel、hook、tape、skill、plugin 和基础 CLI
应用。AgentSeek 添加项目默认值、命令布局、模板和命名，让这个 kernel 成为完整的
workspace 工具。

## 为什么底层是 Bub

Bub 保持小型、面向扩展。这对 AgentSeek 很重要，因为生产选择通常属于具体项目：
存储、channel、model provider、MCP tool、schedule 和 framework bridge。

因此 AgentSeek 可以专注项目生命周期，Bub 保持共同的运行时词汇。

## AgentSeek 改变了什么

AgentSeek 改变 distribution 表面，不改变运行时模型：

- 当对应的 `BUB_*` 未设置时，`AGENTSEEK_*` 会填入匹配的 `BUB_*`。
- `.agentseek/` 是默认 runtime home。
- `.agentseek/agentseek-project/` 是默认 plugin sandbox。
- Bub 命令被组织到面向生命周期的 `agentseek` CLI 下。
- 添加 `create`、`run`、`build`、`deploy` 等项目命令。

## 什么仍然属于 Bub

turn pipeline、channel system、hook model、plugin entry point、tape 语义和
skill discovery 仍然是 Bub 概念。Plugin 作者可以面向 Bub entry point 编写，
并在 AgentSeek 下运行。

## 什么时候使用哪个 CLI

使用 `agentseek` 处理项目工作：模板、workspace 默认值、插件安装、生成项目、
gateway 运行和生命周期命令。

当你需要复现不带 AgentSeek 默认值的上游 Bub 行为，或开发 Bub plugin 并确认它不依赖
AgentSeek 时，直接使用 `bub`。

## 下一步

- [CLI 参考](../reference/cli.zh.md)
- [运行时数据模型](runtime-data-model.zh.md)
- [环境变量参考](../reference/environment.zh.md)
