---
title: 项目生命周期
type: explanation
audience: [A1, A2, A3, A4]
runs: no
verified_on: 2026-06-25
sources:
  - docs/tutorials/02-first-harness-app.zh.md
  - docs/how-to/configure-model.zh.md
  - docs/how-to/run-locally.zh.md
  - docs/how-to/add-skills.zh.md
  - docs/how-to/build-and-deploy.zh.md
  - docs/reference/cli.zh.md
---

# 项目生命周期

这页是 AgentSeek 项目从创建到运行、扩展、交付和运维的地图。每个阶段都链接到负责详细步骤的页面。

## 生命周期地图

| 阶段 | 目标 | 详细页面 |
| --- | --- | --- |
| 创建 | 从维护中的模板生成一个可编辑项目。 | [构建第一个 harness app](tutorials/02-first-harness-app.zh.md) |
| 配置 | 设置模型凭据、provider endpoint 和 runtime environment。 | [配置模型](how-to/configure-model.zh.md)、[环境变量](reference/environment.zh.md) |
| 运行 | 启动本地 app loop、chat path、gateway 或 Compose stack。 | [本地运行](how-to/run-locally.zh.md)、[运行 Gateway](how-to/run-gateway.zh.md)、[Docker Compose](how-to/run-with-docker-compose.zh.md) |
| 扩展 | 添加 skills、MCP tools、plugins、memory 或 channel integrations。 | [添加 Skill](how-to/add-skills.zh.md)、[配置 MCP](how-to/configure-mcp.zh.md)、[安装插件](how-to/install-a-plugin.zh.md)、[使用 ContextSeek](how-to/use-contextseek.zh.md) |
| 构建 | 生成可部署镜像，或预览 build command。 | [构建与部署](how-to/build-and-deploy.zh.md) |
| 部署 | 生成 deployment manifests，或通过 Compose 运行项目。 | [构建与部署](how-to/build-and-deploy.zh.md)、[Docker Compose](how-to/run-with-docker-compose.zh.md) |
| 运维 | 在上线后持续理解 runtime data、paths 和 integrations。 | [运行时数据模型](explanation/runtime-data-model.zh.md)、[文件布局](reference/file-layout.zh.md)、[CLI 参考](reference/cli.zh.md) |

## 阶段如何衔接

`agentseek create` 会生成一个带有独立依赖、源码目录和 `.env.example` 的项目。之后大多数命令都应在生成项目根目录执行，而不是在 AgentSeek 仓库 checkout 中执行。

配置先于本地运行。项目至少需要模型凭据。只有当模板或集成需要时，才继续添加 provider base URL、MCP config、plugin settings 或 storage settings。

运行模式用于回答不同问题。用 `agentseek chat` 检查简单模型路径，用 `agentseek gateway` 处理 channel messages，用 `agentseek run` 启动包含 app loop 或 frontend 的生成项目。当项目或交付路径需要多个服务时，再使用 Docker Compose。

扩展工作通常应留在生成项目内，除非你要修改 AgentSeek 本身。Skills、MCP servers、plugins、ContextSeek 和 contrib packages 是不同扩展入口，让项目可以增长而不重写 runtime core。

构建和部署应发生在项目能本地运行之后。Build command 创建或预览镜像构建；deploy 写出 manifests，便于在其他环境应用前先审查。

运维主要是让 runtime data 保持可解释。运行时数据模型说明 AgentSeek 记录什么；文件布局参考说明状态放在哪里；当需要精确 flags 时再查 CLI 参考。

## 起点

- 新项目：从 [构建第一个 harness app](tutorials/02-first-harness-app.zh.md) 开始。
- 选择 starter：对比 [模板](reference/templates.zh.md) 和 [Hub](hub.zh.md)。
- 已经生成项目：先看 [配置模型](how-to/configure-model.zh.md)，再看 [本地运行](how-to/run-locally.zh.md)。
- 准备交付：使用 [构建与部署](how-to/build-and-deploy.zh.md)。
