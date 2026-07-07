---
title: AgentSeek 生命周期工具包
type: explanation
audience: [A1, A2, A5]
runs: yes
verified_on: 2026-06-26
sources:
  - pyproject.toml
  - README.md
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/lifecycle/core.py
  - templates/index.json
---

# AgentSeek 生命周期工具包

> **简而言之：** AgentSeek 帮你从应用模板走到可运行的本地 AI 应用。
> 它提供一组很小的生命周期命令。

## 先读这里

AgentSeek 为生成出来的应用提供一致的本地开发流程。

它创建应用，检查应用是否就绪，并启动本地开发需要的服务。

```text
AgentSeek CLI
  -> app template
    -> editable generated app
      -> lifecycle tasks
      -> local development stack
```

## 试一个模板路径

安装日常使用的 CLI。

```bash
uv tool install agentseek
```

下面的命令使用一个 Bub 模板。DeepAgents 和 LangChain 模板也使用同一套
生命周期命令形状。运行 `agentseek doctor`
之前先填写 `.env`，否则就绪检查会报告凭证缺失。

```bash
agentseek create bub/default --no-input
cd my_bub_agent
cp .env.example .env
$EDITOR .env
uv sync
npm install --prefix frontend
agentseek doctor
agentseek dev
```

## 生命周期命令

| 命令 | 适用场景 |
| --- | --- |
| `agentseek create` | 从模板创建项目。 |
| `agentseek doctor` | 检查文件、环境、依赖和端口。 |
| `agentseek dev` | 启动生成项目的本地开发栈。 |
| `agentseek info` | 查看项目元数据和本地入口。 |
| `agentseek task` | 直接运行项目定义的任务。 |

## 理解流程

生成出来的项目携带自己的生命周期任务。

AgentSeek 把通用任务暴露为一等命令，也允许你通过 `agentseek task`
运行项目专属任务。

这样工作流保持稳定，而应用行为仍留在生成项目里。

## 当前重点

- 从模板创建可编辑应用。
- 开发前检查本地就绪状态。
- 运行本地开发栈。
- 查看项目元数据和入口。
- 用项目任务扩展应用工作流。

## 继续阅读

- [快速开始](get-started/index.md)
- [创建项目](guides/create-project.md)
- [查看 CLI](reference/cli.md)
