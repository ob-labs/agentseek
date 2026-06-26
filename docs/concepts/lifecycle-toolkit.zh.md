---
title: 生命周期工具包
type: explanation
audience: [A2, A5]
runs: no
verified_on: 2026-06-26
sources:
  - README.md
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/lifecycle/core.py
---

# 生命周期工具包

> **简而言之：** AgentSeek 围绕生成应用标准化开发工作流，
> 但不接管应用自己的运行时。

## 背景

AI 应用模板可能拥有不同的运行时、前端、环境变量和本地服务。

开发者仍需要同一组基础工作流：创建、检查、运行、查看和扩展。

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
