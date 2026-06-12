---
title: 01 — 通过 CLI 快速演示
type: tutorial
audience: [A1]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/env.py
  - pyproject.toml
  - README.zh.md
---

# 通过 CLI 快速演示

你会把 AgentSeek 作为 CLI 工具运行，配置模型，并启动一次本地 chat。

## 1. 安装 CLI

```bash
uv tool install agentseek
```

确认 CLI 可以加载：

```bash
agentseek --help
```

如果能看到 help 页面，工具就准备好了。

## 2. 配置模型

创建一个小工作目录，并写入模型变量：

```bash
mkdir agentseek-demo
cd agentseek-demo
cat > .env <<'EOF'
AGENTSEEK_MODEL=openrouter:free
AGENTSEEK_API_KEY=sk-or-v1-replace-me
AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
EOF
```

如果要得到模型输出，请把 API key 换成真实值。

## 3. 跑一次 chat

```bash
agentseek chat
```

在 `agentseek >` 提示符后输入短 prompt。用 `Ctrl-D` 退出。

如果只想运行单条 prompt：

```bash
agentseek turn "summarize this workspace in one sentence"
```

## 你现在拥有

- 作为 CLI tool 安装的 AgentSeek。
- `.env` 中的模型设置。
- 可以通过 `agentseek chat` 或 `agentseek turn` 走通的本地 runtime 路径。

## 下一步

- 创建可编辑项目：[第一个 harness 应用](02-first-harness-app.zh.md)。
- 查准确参数：[CLI 参考](../reference/cli.zh.md)。
