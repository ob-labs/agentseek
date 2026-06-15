---
title: 02 — 构建你的第一个 harness 应用
type: tutorial
audience: [A2]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/commands/create.py
  - src/agentseek/cli/commands/run.py
  - templates/index.json
  - templates/bub/default/cookiecutter.json
  - templates/bub/default/{{cookiecutter.project_slug}}/pyproject.toml
---

# 构建你的第一个 harness 应用

你会创建一个生成项目，安装它的依赖，并启动本地应用循环。

## 1. 选择 starter

本教程使用 `bub/default`。它是仓库模板目录里最小的完整 harness app。

你可以先查看可用 starter：

```bash
uvx agentseek create --list-templates
```

## 2. 生成项目

选择生成项目所在的工作目录：

```bash
mkdir -p ~/projects
cd ~/projects
uvx agentseek create bub/default --no-input
```

默认项目名是 `my_bub_agent`。

```bash
find my_bub_agent -maxdepth 1 -mindepth 1 -printf "%f\n" | sort
```

你应该看到：

```text
.env.example
Dockerfile
README.md
frontend
pyproject.toml
src
```

## 3. 安装依赖

```bash
cd my_bub_agent
uv sync
npm install --prefix frontend
```

生成项目现在就是你的工作表面。

## 4. 配置模型

```bash
cp .env.example .env
```

打开 `.env`，设置 `AGENTSEEK_API_KEY`。如果你的 provider 需要自定义 endpoint，
也设置 `AGENTSEEK_API_BASE`。

## 5. 本地运行

只检查后端：

```bash
uv run agentseek gateway --enable-channel ag-ui
```

同时启动前端和 gateway：

```bash
uv run agentseek run --no-browser
```

前端 ready 后打开 `http://127.0.0.1:5173`。使用 `Ctrl-C` 停止任一命令。

## 你现在拥有

- 一个有独立 `.venv`、`.env` 和源码树的 standalone project。
- 一条通过 `agentseek run` 启动的本地应用循环。
- 一个可以继续编辑、且不需要改 AgentSeek 仓库的项目。

## 下一步

- 增加本地行为和工具：[添加 skill 和 MCP](03-add-a-skill-and-mcp.zh.md)。
- 使用 Compose 运行：[使用 Docker Compose 运行](../how-to/run-with-docker-compose.zh.md)。
- 查准确参数：[CLI 参考](../reference/cli.zh.md)。
