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
**harness** 环境。如果还没有，请先阅读 `../tutorials/01-quick-demo-cli.md`
与 `../tutorials/02-first-harness-app.md`。

这里沿用总览中的职责拆分：

- **`agentseek`（harness）** —— 运行时 CLI 加可嵌入库；在本仓库 `uv sync`
  之后，或在生成项目里各自 `uv sync` 之后可用。大多数页面以这条路径为主。
- **`agentseek-cli`（项目生命周期 CLI）** —— `create / run / build / deploy
  / api / ctx / skills`；既可以作为路径 A 独立安装，也可以在与 harness 共存时
  合并进同一个 `agentseek` 命令面。

当两条路径都适用时，页面先给出 harness 形式，再给出等价的生命周期命令作为
快捷方式；仅一种路径适用时，页面会显式说明原因。每个条目按统一轮廓组织：
**Use this when… / Prerequisites / Numbered steps**。

## 配置

- `configure-model.md` — 选择 provider、设置密钥、在代码或 CLI 中切换模型。
- `configure-mcp.md` — 将 `mcp.json` 放在 `.agentseek/` 或 `.agents/` 下，并让
  harness 或 CLI 指向它。
- `configure-docker-workspace.md` — 在 Compose 中切换 workspace 挂载、MCP 路径与
  sandbox。

## 扩展

- `install-a-plugin.md` — 用 `agentseek install` 安装插件，并在 harness 中加载。
- `add-skills.md` — 注册项目本地 skill，与随包 skill 共存。
- `add-mcp-server.md` — 编写一条同时被两种形态识别的 MCP 条目。
- `author-a-contrib-plugin.md` — 新建 `contrib/agentseek-<feature>/` 包。

## 运行

- `run-locally.md` — 通过 harness 触发单轮对话，或使用 `agentseek run` 与
  `agentseek chat`。
- `run-gateway.md` — 运行长期驻留的 channel 监听器。
- `run-with-docker-compose.md` — Compose 工作流、挂载与环境变量默认值。
- `build-and-deploy.md` — 用 `agentseek build` 与 `agentseek deploy` 打包并发布。
- `use-contextseek.md` — 在 CLI 中驱动 `agentseek ctx` 流程，并在 harness 中
  消费同一份 context。

## 相关

- 参考：`../reference/index.md`
- 概念：`../explanation/extension-model.md`
