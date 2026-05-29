---
title: 教程
type: tutorial
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - templates/index.json
  - README.md
  - docs/index.md
---

# 教程

教程是面向学习的完整演练。每篇教程都从干净状态开始，端到端跑完，并留给你一份可以保留的具体产物。请挑一篇与你目标匹配的，不要同时浏览三篇。

agentseek 按职责拆成两个互补的包：`agentseek-cli` 负责项目生命周期命令
（`create / run / build / deploy / api / ctx / skills`），`agentseek` 是
harness 本体（运行时 CLI 加可嵌入库）。下面的教程覆盖两条路径：教程 01 直接从
`uv sync` 后的 checkout 运行 harness；教程 02 则先用生命周期 CLI 生成项目，
再在生成项目里落到 harness 环境。

如果你想要的是任务式的食谱（cookbook 风格），请看 [操作指南](../how-to/index.zh.md)。如果你想查询确切的 flag 名称或环境变量别名，请看 [参考](../reference/index.zh.md)。

## 受众矩阵

| 如果你是…… | 从这里开始 | 然后 |
| --- | --- | --- |
| A1 —— 初次评估者 | [通过 CLI 快速演示](01-quick-demo-cli.zh.md) | [agentseek 是什么](../explanation/what-agentseek-is.zh.md) |
| A2 —— 在 agentseek 之上构建应用 | [构建你的第一个 harness 应用](02-first-harness-app.zh.md) | [添加一个 skill 和一个 MCP server](03-add-a-skill-and-mcp.zh.md)，然后 [操作指南](../how-to/index.zh.md) |
| A3 —— 编写 plugin 或集成 | [构建你的第一个 harness 应用](02-first-harness-app.zh.md)（了解 runtime 形状） | [运行时数据模型](../explanation/runtime-data-model.zh.md)，[如何编写一个 contrib plugin](../how-to/author-a-contrib-plugin.zh.md) |
| A4 —— 运维部署 | [添加一个 skill 和一个 MCP server](03-add-a-skill-and-mcp.zh.md) | [如何使用 Docker Compose 运行](../how-to/run-with-docker-compose.zh.md)，[环境变量参考](../reference/environment.zh.md) |
| A5 —— 只是好奇 | 跳过教程 | [agentseek 是什么](../explanation/what-agentseek-is.zh.md) |

## 三篇教程

1. **[通过 CLI 快速演示](01-quick-demo-cli.zh.md) —— 通过 CLI 快速体验。** 五分钟的评估者路径：clone、`uv sync`、设置三个环境变量、运行 `agentseek chat`。这对应总览里的**路径 B**：从已同步的 checkout 直接运行 harness 的运行时 CLI。适合评估 agentseek、跑本地一次性流程，或排查 runtime。
2. **[构建你的第一个 harness 应用](02-first-harness-app.zh.md) —— 你的第一个 harness 应用。** 面向应用开发者的路径。先用 `agentseek create`（由 `agentseek-cli` 提供）生成项目，再在生成项目里执行 `uv sync`，把 harness 本体解析进去。看完这一页之后，你持续编辑的就是这个生成出来的项目，而不是 clone 下来的仓库。
3. **[添加一个 skill 和一个 MCP server](03-add-a-skill-and-mcp.zh.md) —— 添加一个 skill 和一个 MCP server。** 运维形态：在 `.agents/skills/<name>/SKILL.md` 下放一个项目本地的 skill，在 `.agents/mcp.json`（或 `.agentseek/mcp.json`）里注册一个 MCP server，然后看着运行中的 agent 把两者都识别出来。

## 基础约定

- 教程假设你使用 Python 3.12+、[uv](https://docs.astral.sh/uv/) 以及类 Unix shell。Windows 可通过 WSL2 使用。
- 除非教程另有说明，所有命令都从仓库根目录原样执行。如果某条命令失败，请先修好再继续 —— 后续步骤都假设前一步已经成功。
- 示例中的 API key 明显是占位符（`sk-or-v1-…`）。在你期望真实模型输出前，请替换为真实值。
- 这些页面在 front-matter 标注的日期当天，针对真实仓库验证过。如果日期过旧，请提 issue，不要猜测。
