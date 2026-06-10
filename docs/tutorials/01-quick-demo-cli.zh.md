---
title: 01 — 通过 CLI 快速演示
type: tutorial
audience: [A1]
runs: yes
verified_on: 2026-06-08
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/env.py
  - pyproject.toml
  - README.md
---

# 通过 CLI 快速演示

你会 clone 仓库、安装依赖、配置模型，并通过 `agentseek chat` 跑通一次 chat。

## 1. Clone 并安装

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
```

确认 CLI 可用：

```bash
uv run agentseek --help
```

你应该看到项目管理命令（`create`、`run`、`build`、`deploy`）、运行时命令（`chat`、
`turn`、`gateway`）和扩展命令（`plugin`、`ctx`、`skills`、`api`）。

## 2. 配置模型

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-replace-me
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
```

把 API key 替换成真实值。也可以复制 `.env.example` 后编辑文件：

```bash
cp .env.example .env
```

## 3. 启动 chat

```bash
uv run agentseek chat
```

在 `agentseek >` 提示符后输入短 prompt。用 `Ctrl+D` 或配置的退出命令结束。

如果只想跑单条 prompt：

```bash
uv run agentseek turn "summarize this workspace in one sentence"
```

## 你现在拥有

- 已同步的仓库环境。
- 通过 `AGENTSEEK_*` 或 `.env` 配置好的模型。
- 可用的 `agentseek chat` 或 `agentseek turn`。

## 下一步

- 构建应用项目：[构建你的第一个 harness 应用](02-first-harness-app.zh.md)。
- 查看可用命令：[CLI 参考](../reference/cli.zh.md)。
