---
title: 生命周期工具包
type: explanation
audience: [A2, A5]
runs: no
verified_on: 2026-07-07
sources:
  - README.md
  - docs/get-started/index.zh.md
  - docs/guides/create-project.zh.md
  - docs/guides/inspect-project.zh.md
  - docs/guides/check-project.zh.md
  - docs/guides/run-local-development.zh.md
  - docs/guides/run-project-tasks.zh.md
  - docs/reference/lifecycle-spec.zh.md
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/lifecycle/core.py
---

# 生命周期工具包

> **简而言之：** AgentSeek 围绕生成应用标准化开发工作流，
> 但不接管应用自己的运行时。

## 背景

AI 应用模板可能拥有不同的运行时、前端、环境变量和本地服务。

开发者仍需要同一组基础工作流：创建、检查、运行、查看和扩展。

## 生命周期地图

| 阶段 | 目标 | 主要命令 | 详细页面 |
| --- | --- | --- | --- |
| 创建 | 从维护中的模板生成可编辑应用。 | `agentseek create` | [创建项目](../guides/create-project.zh.md) |
| 查看 | 理解服务、入口、环境检查和任务。 | `agentseek info` | [查看项目](../guides/inspect-project.zh.md) |
| 配置 | 填写必需环境值并安装项目依赖。 | 项目工具 | [快速开始](../get-started/index.zh.md) |
| 检查 | 启动服务前验证本地就绪状态。 | `agentseek doctor` | [检查项目](../guides/check-project.zh.md) |
| 运行 | 启动或预览模板定义的本地工作流。 | `agentseek dev` | [运行本地开发](../guides/run-local-development.zh.md) |
| 扩展 | 添加或调整项目定义的生命周期任务。 | `agentseek task` | [运行项目任务](../guides/run-project-tasks.zh.md) |

执行 `agentseek create` 后，大多数生命周期命令都应在生成项目根目录中运行。生成项目拥有 `.agentseek/lifecycle.toml` 文件，由它告诉 AgentSeek 有哪些服务、检查和任务。

## 工作方式

AgentSeek 提供命令表面。每个生成项目提供生命周期行为。

```text
stable command
  -> project lifecycle spec
    -> template-specific behavior
```

## 为什么这样设计

命令表面在不同模板之间保持可预测。

生成应用保留对运行时细节的控制权。这样模板可以自由演进，
不需要为每个运行时选择增加新的 AgentSeek 命令。

## 对用户的影响

- 你在不同模板中使用同一组 AgentSeek 命令。
- 你在生成项目内部检查和修改应用行为。
- 当模板暴露额外项目任务时，你使用 `agentseek task`。
- 需要精确字段语义时，可以查看[生命周期规范参考](../reference/lifecycle-spec.zh.md)。
