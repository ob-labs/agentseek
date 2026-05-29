---
title: 02 —— 构建你的第一个 harness 应用
type: tutorial
audience: [A2]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - contrib/agentseek-cli/pyproject.toml
  - templates/index.json
  - templates/bub/default/cookiecutter.json
  - templates/bub/default/{{cookiecutter.project_slug}}/README.md
  - templates/bub/default/{{cookiecutter.project_slug}}/pyproject.toml
  - templates/bub/default/{{cookiecutter.project_slug}}/src/{{cookiecutter.project_slug}}/dev.py
  - docs/index.md
---

# 构建你的第一个 harness 应用

> **你将完成：** 从 `bub/default` 模板生成一个新项目，把它作为独立的 Python 包安装，并运行一个**你自己**端到端掌控的 agent —— 前端、gateway、配置全都归你。
> **你需要：** Python 3.12+、[uv](https://docs.astral.sh/uv/) 和一个模型提供方的 API key。只有当你还想用上自带的 CopilotKit 前端时，才需要 Node.js + npm；教程会在涉及到时明确指出。

本教程会把总览里的两条路径串起来：先用**项目生命周期 CLI** `agentseek-cli`
提供的 `agentseek create` 生成项目，再切到生成项目里执行自己的 `uv sync`，
把 **harness** 本体解析进去。之后你持续编辑的就是这个生成出来的项目。教程 03
会基于它继续构建，所以结束时别删掉它。

## 1. 从模板生成项目

agentseek 在 `templates/` 下自带了若干起步模板。每个模板组合了一个框架选择（`bub`、`langchain`、`deepagents`）和一种风味（`default`、`cli-remote`、……）。一条命令就能列出目录：

```bash
uv run agentseek create --list-templates
```

```text title="expected output"
Available deepagents templates:
  default  Local create_deep_agent runnable bound to agentseek-langchain.
Available langchain templates:
  cli-remote  Remote LangGraph CLI agent bridged via LangGraphClientRunnable.
  default     LangChain create_agent + CopilotKit middleware over agentseek-langchain.
Available bub templates:
  default  Lightweight Bub agent: agentseek gateway + CopilotKit frontend, no LangChain.
```

本教程使用 **`bub/default`**，因为它是经过 harness 最轻量的路径（依赖图里没有 LangChain，没有远程 runtime）。请选择一个**位于本 checkout 之外**的工作目录 —— 模板生成的是同级项目，而不是子目录。

`create` 命令属于 `agentseek-cli`
（`contrib/agentseek-cli/pyproject.toml:17-21`）。本教程直接从已同步的仓库环境里调用它，是因为教程 01 已经准备好了这个环境；独立的路径 A 等价做法是 `uv tool install agentseek-cli`。

```bash
mkdir -p ~/projects && cd ~/projects
uv run --project ~/code/agentseek agentseek create bub --template default --no-input
```

`--no-input` 会接受模板 `cookiecutter.json` 中的所有默认值，得到一个名为 `my_bub_agent` 的项目。想要交互式提示（项目名、端口、作者），就去掉这个 flag。

把 `~/code/agentseek` 换成你在教程 01 里 clone agentseek 的实际路径即可。

命令成功时输出很少。验证一下目录结构：

```bash
ls -a my_bub_agent
```

```text title="expected output"
Dockerfile   .env.example   frontend   pyproject.toml   README.md   src
```

你现在拥有一个真实的 Python 包：它的 `pyproject.toml` 把 `agentseek` 和 `agentseek-ag-ui` 列为依赖，`src/my_bub_agent/dev.py` 是一个 supervisor，会拉起 gateway 加前端，`frontend/` 目录则是一个 CopilotKit 的 Next.js 应用。模板自带的 README 也在项目根目录。

## 2. 安装项目自身的依赖

生成的项目就是一个普通的 `uv` 项目。在项目根目录：

```bash
cd my_bub_agent
uv sync
```

这会在 `my_bub_agent/` 里（而不是在 agentseek checkout 里）创建一个 `.venv/`，并安装 `agentseek`、`agentseek-ag-ui` 和其它列出的依赖。如果你是从本地源码 checkout 生成的项目，`pyproject.toml` 已经通过 `[tool.uv.sources]` 指向它了 —— 完整对照表见 `../reference/templates.md`。

## 3. 配置模型

模板自带 `.env.example`。复制它。

```bash
cp .env.example .env
```

你拿到的默认值（与模板逐字一致）：

```text title=".env.example"
AGENTSEEK_MODEL=openai:gpt-4o-mini
AGENTSEEK_API_KEY=
AGENTSEEK_API_BASE=
AGENTSEEK_STREAM_OUTPUT=true
AGENTSEEK_AG_UI_PORT=8088
FRONTEND_PORT=5173
COPILOTKIT_PORT=4000
AGENTSEEK_AG_UI_AGENT_URL=http://127.0.0.1:8088/agent
```

填入 `AGENTSEEK_API_KEY`（如果你不用 OpenAI，再填 `AGENTSEEK_API_BASE`）。模型也可以换 —— `openrouter:free`、`openai:qwen-plus` 等等。变量名和 CLI 用的是同一套，因为模板依赖的是同一个 agentseek 发行版。完整参考在 `../reference/environment.md`。

## 4. 运行 gateway

模板的 `dev.py` supervisor 预期 CopilotKit 前端在场。如果只想做后端冒烟测试，跳过前端部分，直接跑 gateway：

```bash title="not executed in this run"
uv run agentseek gateway --enable-channel ag-ui
```

改在仓库 checkout 里跑一条命令，确认它的形状：

```bash
uv run agentseek gateway --help
```

```text title="expected output"
 Usage: agentseek gateway [OPTIONS]

 Start message listeners(like telegram).

 --enable-channel        TEXT  Channels to enable for CLI (default: all)
 --help                        Show this message and exit.
```

完整开发路径（前端 + gateway）需要 `npm`。在项目根目录：

```bash title="not executed in this run"
npm install --prefix frontend
uv run agentseek run --no-browser
```

`agentseek run`（由 `agentseek-cli` contrib 包提供，见 `../reference/cli.md`）包装了 `src/my_bub_agent/dev.py` 中的 supervisor。它会在 `AGENTSEEK_AG_UI_PORT`（默认 `8088`）上启动 gateway，在 `FRONTEND_PORT`（默认 `5173`）上启动 CopilotKit 支持的前端。两个进程都报告 ready 之后，在浏览器中打开 `http://127.0.0.1:5173`，发一轮对话。

## 5. 确认这个 agent 是你的

打开 `src/my_bub_agent/dev.py`，看看 supervisor（第 88–119 行）：gateway 是用 `agentseek gateway --enable-channel ag-ui` 拉起的，前端用的是 `npm run dev`，两者在收到 `SIGINT`/`SIGTERM` 时都会被回收。这套流程没有任何部分被锁死在 agentseek 仓库上 —— 你可以编辑这个文件、修改 channel、换掉前端，或者完全删掉前端，从别处调用 gateway。harness 是你的。

模型路由决策位于 `agentseek-ag-ui`（一个 contrib 包）和 `agentseek` 发行版本身；一轮对话如何从 channel 经过 runtime 走到模型，见 `../explanation/runtime-data-model.md`。

## 你现在拥有什么

- 一个独立的项目目录（按默认值就是 `~/projects/my_bub_agent`），有自己的 `pyproject.toml`、`.venv/` 和 `src/` 布局。
- 一个已填好的 `.env`，指向真实模型。
- 已确认 `agentseek create` 和 `agentseek gateway` 的形状。
- 一个清晰的认识：`agentseek create` 只是入口步骤；`uv sync` 之后，你持续编辑的是这个生成出来的项目，而不是 clone 下来的 `agentseek` 仓库。

## 接下来去哪

- 给你刚生成的项目加一个本地 skill 和一个 MCP server：`03-add-a-skill-and-mcp.md`。
- 在不破坏项目的前提下切换模型提供方：`../how-to/configure-model.md`。
- 查阅 `agentseek create`、`agentseek gateway` 和 `agentseek run` 的每个 flag：`../reference/cli.md`。
- 看完整模板列表和每个模板带了什么：`../reference/templates.md`。
- 在 Docker Compose 下运行同一个项目：`../how-to/run-with-docker-compose.md`。
