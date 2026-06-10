---
title: agentseek 是什么
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-06-08
sources:
  - README.md
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/surface.py
---

# agentseek 是什么

AgentSeek 是一个 database-native agent harness，提供一个 CLI 入口和可嵌入的 Python
运行时。它帮助团队构建、运行和运维 agent 应用，让运行时数据从第一轮开始就是持久、
可查询、可回放、可评估的。

公开命令面是：

- `agentseek create/run/build/deploy`：项目管理。
- `agentseek chat/turn/gateway`：运行时执行。
- `agentseek plugin/ctx/skills/api`：扩展和服务桥接。

## 背景

Agent 数据很容易在 demo 后散落：session context、tool calls、logs、eval artifacts、
feedback、traces 进入不同系统。AgentSeek 的假设相反：这些运行时事实应该从一开始就
共享同一个持久 substrate。

这个 substrate 自然是数据库。Harness 的意义是让团队保留已有 agent framework，同时
采用一个把运行时数据视为一等工作负载的运行层。

## 工作方式

1. **Bub** 提供 hook-first runtime kernel：channels、turns、tapes、skills、plugins
   和基础 CLI 行为。
2. **AgentSeek** 叠加产品默认值：`.agentseek/` runtime home、环境变量别名、
   onboarding branding、插件 sandbox、命令布局、项目命令和内置 skills。
3. **Contrib 包与应用代码** 增加存储后端、LangChain bridge、UI adapter、context
   system、schedule，以及真正的业务应用。

## 设计选择

- **Harness，不是 framework。** AgentSeek 不规定 agent 怎么写；LangChain、
  DeepAgents、Bub-native app 或自定义 orchestrator 都可以跑在上面。
- **Database-native，不是 database-coupled。** 本地 SQLite 适合开发；需要规模或兼容性时，
  可以通过 contrib 包引入 OceanBase-backed storage。
- **一个入口。** 项目命令和运行时命令共享 `agentseek`，用户不需要记住哪个包或二进制
  负责哪个任务。
- **Bub 在下面。** AgentSeek 组合 Bub，而不是隐藏 Bub。需要上游行为时仍然可以直接使用 Bub。

## 非目标

AgentSeek 不试图替代 agent framework、成为通用插件市场、提供 hosted SaaS 或强制某个 UI。
它提供 harness 和运行时 substrate；应用和部署选择保持显式。

## 相关

- [命令概览](cli-surface.zh.md)
- [AgentSeek 与 Bub 的关系](bub-relationship.zh.md)
- [AgentSeek 与 LangChain 的关系](langchain-relationship.zh.md)
- [运行时数据模型](runtime-data-model.zh.md)
