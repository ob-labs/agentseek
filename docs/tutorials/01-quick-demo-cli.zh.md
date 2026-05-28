---
title: 01 —— 通过 CLI 快速演示
type: tutorial
audience: [A1]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - src/agentseek/env.py
  - pyproject.toml
  - README.md
---

# 通过 CLI 快速演示

> **你将完成：** clone 仓库、安装依赖、把 agentseek 指向一个模型，并从自带的 `agentseek chat` REPL 收到一轮聊天回复。
> **你需要：** Python 3.12+、[uv](https://docs.astral.sh/uv/)、`git`，以及一个模型提供方的 API key（OpenAI、OpenRouter、DashScope 等）。

这一页的目的是让你在大约五分钟内确认 agentseek 是真实可用的。它**不是**在你自己的应用里使用 agentseek 的推荐方式。CLI 是一个 Bub 兼容的入口，会加载仓库自身的配置；要把 agentseek 嵌入你自己的项目，看完本页后请直接跳到 `02-first-harness-app.md`。

## 1. Clone 并安装

把仓库拉到本地，让 `uv` 解析 lockfile。

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
```

`uv sync` 会在仓库根目录创建 `.venv/`，并以可编辑模式安装 `agentseek` 发行版及其传递依赖。从此以后，`uv run agentseek …` 跑的就是本次 checkout 中的 agentseek 版本。

确认 CLI 能加载。

```bash
uv run agentseek --help
```

```text title="expected output"
 Usage: agentseek [OPTIONS] COMMAND [ARGS]...

 Batteries-included, hook-first AI framework

 Commands
   run        Start the project locally after completing .env configuration.
   chat
   onboard    Interactively collect plugin configuration and write it to Bub's
              config file.
   gateway    Start message listeners(like telegram).
   install    Install a plugin into Bub's environment, or sync the environment
              if no specifications are provided.
   uninstall  Uninstall a plugin from Bub's environment.
   update     Update selected package or all packages in Bub's environment.
   create     Create a new agent project from a pre-built template.
   build      Build the project into a container image (wraps `docker build` /
              `docker buildx build`).
   deploy     Generate deployment manifests (docker-compose / k8s).
   api        Forward API runtime commands to `agentseek-api` when it is
              installed.
   ctx        ContextSeek — semantic context layer (forwarded to the
              `contextseek` CLI).
   skills     Manage agent skills via the upstream `vercel-labs/skills` CLI.
   login      Authentication related commands
```

你现在应该看到 `Commands` 表，其中至少列出 `run`、`chat`、`create` 和 `install`。如果看到的是 Python traceback，请就此停下，修好 import 错误再继续。

## 2. 把 agentseek 指向一个模型

agentseek 读取 `AGENTSEEK_*` 变量，并以 `BUB_*` 别名转发给底层的 Bub runtime。映射定义在 `src/agentseek/env.py`（`apply_agentseek_env_aliases`）。完整的优先级规则见 `../reference/environment.md`。

导出 CLI 演示需要的三个变量：

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-replace-me              # placeholder, replace with a real key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
```

这个 API key 是占位符 —— 没有它 agentseek 也能启动，但你一按回车，模型调用就会失败。在继续之前请替换成真实 key。

如果你更喜欢用文件而非 shell export，复制 `.env.example` 并编辑；agentseek 会通过 [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) 自动读取 `.env`。

```bash
cp .env.example .env
```

## 3. 启动一轮对话

运行 chat REPL。

```bash
uv run agentseek chat
```

```text title="expected output"
INFO     | channel.manager started listening
╭──────────────── Bub ────────────────╮
│ workspace: /…/agentseek             │
│ model: openai:qwen-plus             │
│ internal command prefix: ','        │
│ shell command prefix: ',' at line start (Ctrl-X for shell mode)
│ type ',help' for command list
╰─────────────────────────────────────╯
agentseek >
```

`model:` 这一行会显示你在第 2 步设置的值 —— 上面的 `openai:qwen-plus` 只是本地 checkout 当时碰巧配置的内容。在 `agentseek >` 提示符下输入一句简短的 prompt，按回车，你应该会看到回复以流式方式返回。用 `Ctrl+D` 或输入 `,quit` 退出。

> **单次执行变体。** 如果你只想跑一条 prompt 而不进入 REPL，可以用 `uv run agentseek run "summarize this workspace in one sentence"`。注意 `agentseek run` 属于 `agentseek-cli` contrib 包，并桥接到上游 Bub 的 `run` 行为；完整接口见 `../reference/cli.md`。

## 你现在拥有什么

- 仓库根目录下一个可用的 `.venv/`，里面装好了 agentseek 发行版。
- 指向真实模型的三个 `AGENTSEEK_*` 环境变量（或填好的 `.env`）。
- 一次经由你的模型提供方完成的 `agentseek chat` REPL 往返。

## 接下来去哪

- 想在**你自己**的应用里跑 agentseek 而不是用自带 CLI，请继续 `02-first-harness-app.md`。那是主要的上手路径。
- 想了解为什么演示使用 `.agentseek/` 存放本地状态，以及别名模型如何工作，请读 `../explanation/bub-relationship.md`。
- 想查阅每个 CLI flag 或环境变量而不是死记硬背，请看 `../reference/cli.md` 和 `../reference/environment.md`。
