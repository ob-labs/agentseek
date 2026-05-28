---
title: 操作指南索引
type: how-to
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
---

# 操作指南

任务导向的实操指引。每个页面都假设你已经具备一个可用的 agentseek
安装。如果还没有，请先阅读 `../tutorials/01-quick-demo-cli.md` 与
`../tutorials/02-first-harness-app.md`。

操作指南优先采用 **库 / 配置文件形式**，并在适用时附上简短的
`### CLI 快捷方式` 段落。CLI 是演示入口，并非推荐的产品入口
(参见 `../explanation/choosing-an-entry-point.md`)。

## 配置

- `configure-model.md` — 选择 provider、设置密钥、切换模型。
- `configure-mcp.md` — 将 `mcp.json` 放在 `.agentseek/` 或 `.agents/` 下。
- `configure-docker-workspace.md` — 在 Compose 中切换 workspace 挂载、MCP 路径与
  sandbox。

## 扩展

- `install-a-plugin.md` — `agentseek install` 与 plugin sandbox。
- `add-skills.md` — 项目本地 skill 与随包 skill 的差异。
- `add-mcp-server.md` — 编写一条 MCP 条目。
- `author-a-contrib-plugin.md` — 新建 `contrib/agentseek-<feature>/` 包。

## 运行

- `run-locally.md` — `agentseek run` 与 `agentseek chat`。
- `run-gateway.md` — 长期运行的 channel 监听器。
- `run-with-docker-compose.md` — Compose 工作流、挂载与环境变量默认值。
- `build-and-deploy.md` — `agentseek build` 与 `agentseek deploy`。
- `use-contextseek.md` — `agentseek ctx` 流程。

## 相关

- 参考: `../reference/index.md`
- 概念: `../explanation/extension-model.md`
