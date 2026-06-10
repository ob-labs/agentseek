---
title: 02 — 构建你的第一个 harness 应用
type: tutorial
audience: [A2]
runs: yes
verified_on: 2026-06-08
sources:
  - src/agentseek/cli/commands/new.py
  - src/agentseek/cli/commands/dev.py
  - templates/index.json
  - templates/bub/default/cookiecutter.json
  - templates/bub/default/{{cookiecutter.project_slug}}/pyproject.toml
---

# 构建你的第一个 harness 应用

你会使用 `agentseek create` 创建项目、同步生成项目、配置模型，并在本地运行它。

## 1. 选择模板

列出内置模板：

```bash
uv run agentseek create --list-templates
```

本教程使用 `bub/default`，因为它是最轻量的完整 harness app。

## 2. 生成项目

选择 AgentSeek checkout 之外的工作目录：

```bash
mkdir -p ~/projects
cd ~/projects
uvx agentseek create bub/default --no-input
```

默认项目名是 `my_bub_agent`。

```bash
ls -a my_bub_agent
```

期望形态：

```text
Dockerfile   .env.example   frontend   pyproject.toml   README.md   src
```

## 3. 安装项目依赖

```bash
cd my_bub_agent
uv sync
```

生成项目依赖 `agentseek`，拥有与仓库 checkout 相同的 CLI 命令组。

## 4. 配置模型

```bash
cp .env.example .env
```

填入 `AGENTSEEK_API_KEY`，必要时填入 `AGENTSEEK_API_BASE`。完整表见
[环境变量参考](../reference/environment.zh.md)。

## 5. 本地运行

后端 smoke test：

```bash title="not executed in this run"
uv run agentseek gateway --enable-channel ag-ui
```

完整 frontend + gateway 循环：

```bash title="not executed in this run"
npm install --prefix frontend
uv run agentseek run --no-browser
```

前端 ready 后打开 `http://127.0.0.1:5173`。

## 你现在拥有

- 一个有独立 `.venv`、`.env` 和源码树的 standalone project。
- 通过 `agentseek create` 和 `agentseek run` 验证过的项目命令路径。
- 一个可以继续编辑、且不需要改 AgentSeek 仓库的应用项目。

## 下一步

- 增加项目行为：[添加 skill 和 MCP](03-add-a-skill-and-mcp.zh.md)。
- 使用 Compose 运行：[使用 Docker Compose 运行](../how-to/run-with-docker-compose.zh.md)。
- 查看所有选项：[CLI 参考](../reference/cli.zh.md)。
