---
title: 教程
type: tutorial
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - templates/index.json
---

# 教程

教程是面向学习的完整演练。每篇教程都从干净的状态开始，端到端地跑完，并留给你一个可以保留的具体产物。请挑选与你目标匹配的页面，不要同时浏览三篇。

如果你想要的是任务式的食谱（cookbook 风格），请看 `../how-to/index.md`。如果你想查询确切的 flag 名称或环境变量别名，请看 `../reference/index.md`。

## 受众矩阵

| 如果你是…… | 从这里开始 | 然后 |
| --- | --- | --- |
| A1 —— 初次评估者 | `01-quick-demo-cli.md` | `../explanation/what-agentseek-is.md` |
| A2 —— 在 agentseek 之上构建应用 | `02-first-harness-app.md` | `03-add-a-skill-and-mcp.md`，然后 `../how-to/` |
| A3 —— 编写 plugin 或集成 | `02-first-harness-app.md`（了解 runtime 形状） | `../explanation/runtime-data-model.md`，`../how-to/author-a-contrib-plugin.md` |
| A4 —— 运维部署 | `03-add-a-skill-and-mcp.md` | `../how-to/run-with-docker-compose.md`，`../reference/environment.md` |
| A5 —— 只是好奇 | 跳过教程 | `../explanation/what-agentseek-is.md` |

## 三篇教程

1. **`01-quick-demo-cli.md` —— 通过 CLI 快速演示。** 五分钟的评估者路径：clone、`uv sync`、设置三个环境变量、运行 `agentseek chat`。这一页是演示入口。它**故意不是**在真实项目里使用 agentseek 的推荐方式；那条路径在教程 02。
2. **`02-first-harness-app.md` —— 你的第一个 harness 应用。** 主要的上手教程。从内置模板生成项目、同步依赖、端到端运行一个由你自己掌控的 agent。看完这一页之后，harness/library 形态就是你大部分时间会待的界面。
3. **`03-add-a-skill-and-mcp.md` —— 添加一个 skill 和一个 MCP server。** 运维形态：在 `.agents/skills/<name>/SKILL.md` 下放一个项目本地的 skill，在 `.agents/mcp.json`（或 `.agentseek/mcp.json`）里注册一个 MCP server，然后看着运行中的 agent 把两者都识别出来。

## 基础约定

- 教程假设你使用 Python 3.12+、[uv](https://docs.astral.sh/uv/) 以及类 Unix shell。Windows 可通过 WSL2 使用。
- 除非教程另有说明，否则所有命令都从仓库根目录原样执行。如果某条命令失败，请先修好再继续 —— 后续步骤都假设前一步成功了。
- 示例中的 API key 明显是占位符（`sk-or-v1-…`）。在你期望真实模型输出前，请替换为真实值。
- 这些页面在 front-matter 中标注的日期当天，针对真实仓库验证过。如果日期过旧，请提 issue，不要猜测。
