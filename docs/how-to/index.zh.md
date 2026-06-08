---
title: 操作指南索引
type: how-to
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - README.md
  - docs/index.md
---

# 操作指南

面向运维者与集成方的任务导向指引。每个页面都假设你已经具备一个可用的
**harness** 环境。如果还没有，请先阅读
[通过 CLI 快速演示](../tutorials/01-quick-demo-cli.zh.md) 与
[构建你的第一个 harness 应用](../tutorials/02-first-harness-app.zh.md)。

这里沿用总览中的职责拆分：

- **`agentseek`（harness）** —— 运行时 CLI 加可嵌入库；在本仓库 `uv sync`
  之后，或在生成项目里各自 `uv sync` 之后可用。大多数页面以这条路径为主。
- **`agentseek-cli`（项目生命周期 CLI）** —— `new / dev / build / deploy / api / ctx / skills`；既可以作为路径 A 独立安装，也可以在与 harness 共存时
  合并进同一个 `agentseek` 命令面。

当两条路径都适用时，页面先给出 harness 形式，再给出等价的生命周期命令作为
快捷方式；仅一种路径适用时，页面会显式说明原因。每个条目按统一轮廓组织：
**何时使用… / 前提条件 / 编号步骤**。

## 配置

- [如何配置模型提供方](configure-model.zh.md) — 选择 provider、设置密钥、在代码或 CLI 中切换模型。
- [如何配置 MCP 服务器](configure-mcp.zh.md) — 将 `mcp.json` 放在 `.agentseek/` 或 `.agents/` 下，并让
  harness 或 CLI 指向它。
- [如何配置 Docker workspace](configure-docker-workspace.zh.md) — 在 Compose 中切换 workspace 挂载、MCP 路径与
  sandbox。

## 扩展

- [如何安装插件](install-a-plugin.zh.md) — 用 `agentseek plugin install` 安装插件，并在 harness 中加载。
- [如何添加 skill](add-skills.zh.md) — 注册项目本地 skill，与随包 skill 共存。
- [如何添加 MCP 服务器](add-mcp-server.zh.md) — 编写一条同时被两种形态识别的 MCP 条目。
- [如何编写一个 contrib plugin](author-a-contrib-plugin.zh.md) — 新建 `contrib/agentseek-<feature>/` 包。

## 运行

- [如何在本地运行 agentseek](run-locally.zh.md) — 用 `agentseek dev` 启动生成项目，
  用 `agentseek turn` 触发单轮运行时调用，或使用 `agentseek chat`。
- [如何运行 gateway](run-gateway.zh.md) — 运行长期驻留的 channel 监听器。
- [如何使用 Docker Compose 运行](run-with-docker-compose.zh.md) — Compose 工作流、挂载与环境变量默认值。
- [如何构建与部署](build-and-deploy.zh.md) — 用 `agentseek build` 与 `agentseek deploy` 打包并发布。
- [如何使用 ContextSeek](use-contextseek.zh.md) — 在 CLI 中驱动 `agentseek ctx` 流程，并在 harness 中
  消费同一份 context。

## 相关

- 参考：[参考](../reference/index.zh.md)
- 概念：[扩展模型](../explanation/extension-model.zh.md)
