---
title: 选择一个入口
type: explanation
audience: [A1, A2, A4, A5]
runs: no
verified_on: 2026-05-29
sources:
  - README.md
  - docs/index.md
  - pyproject.toml
  - contrib/agentseek-cli/pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli.py
  - contrib/agentseek-cli/src/agentseek_cli/standalone.py
  - contrib/agentseek-cli/src/agentseek_cli/plugin.py
  - entrypoint.sh
---

# 选择一个入口

> **一句话：**agentseek 以**两个 PyPI 包**形式提供，按职责拆分 ——
> `agentseek-cli` 是**项目生命周期 CLI**（scaffold、run、build、deploy）；
> `agentseek` 是 **harness** 本身（chat、gateway、运行时、可嵌入的库）。按你
> 的工作来选。Docker Compose 与 contrib 包是 harness 之上的*部署 / 扩展面*，
> 不是另外的入口。

## 背景

人们以不同方式遇见 agentseek：有人只想在 laptop 或 CI 里生成一个项目，根本
不需要 harness 在 host 上；有人想本地起一个 chat REPL 或 gateway 调试一轮；
有人把 harness 嵌进已有的服务里；有人在容器里运行长进程 gateway。两个包的
存在，是让前两类人有一个干净、隔离的入口；后两类人则是用不同启动器跑同一个
harness。

本页把两条路径的差异写清楚，让选择回到"合不合适"，而不是"哪个更正式"。

## 两条路径

### 路径 A —— `agentseek-cli`（项目生命周期 CLI）

直接从 PyPI 安装：

```bash
uv tool install agentseek-cli
```

`uv tool install` 会为 `agentseek-cli` 创建一个隔离 venv，并暴露一个名为
`agentseek` 的 console script。Typer app 由
`agentseek_cli.app.build_app()`
（`contrib/agentseek-cli/src/agentseek_cli/app.py:33-43`）构建，只包含项目
生命周期组：

`create / run / build / deploy / api / ctx / skills`。

适合路径 A 的场景：

- 你想用 `agentseek create …` **生成项目**，而且不想为此 clone 整个仓库。
- 你管理只跑 `build` / `deploy` 的 **CI** —— 不需要把 harness 运行时拉进来。
- 你在 harness 环境之外管理项目：`run`、构建镜像、生成部署清单、调用 `ctx`
  / `skills`。

路径 A 故意**不**包含 harness 运行时 CLI（`chat / gateway / install / …`）。
依赖树很小，从 PyPI 解析很干净。

### 路径 B —— `agentseek`（harness）

harness 是一个普通的 Python 项目，但**不能**直接从 PyPI 安装：`requires-dist`
里有 `bub-feishu`、`bub-mcp` 与 `agentseek-schedule-sqlalchemy`，它们通过
`[tool.uv.sources]` 接到 git source / workspace，而 PyPI metadata 无法携带
source 覆盖。因此 `pip install agentseek` 与 `uv tool install agentseek` 都
会解析失败。请使用一个自带这些 source 的项目：

```bash
# 方式 1 —— 克隆本仓库。
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync

# 方式 2 —— 用路径 A 生成项目，再在里面 sync。
uv tool install agentseek-cli
agentseek create bub --template default --no-input
cd my_bub_agent
uv sync
```

两种方式下，`uv run agentseek` 最终都调用
`agentseek.__main__:app`（`pyproject.toml:49`、
`src/agentseek/__main__.py:52-69`），它启动 `BubFramework`、加载所有 Bub
plugin，并暴露 **harness 运行时**命令面：

`chat / run / gateway / install / uninstall / update / mcp / login / onboard`。

适合路径 B 的场景：

- 你想端到端**评估**项目 ——
  [01 —— 通过 CLI 快速演示](../tutorials/01-quick-demo-cli.zh.md)
  是最短的路。
- 你把 harness **嵌**进自己的应用。`agentseek` 就是一个普通 Python 包，
  harness 在你应用启动时随之启动。详见
  [02 —— 构建你的第一个 harness 应用](../tutorials/02-first-harness-app.zh.md)。
- 你跑**长进程**工作负载 —— 本地 `gateway`、MCP server、或 Bub 插件开发。

### 两者共存 —— 同名、合并表面

当 `agentseek-cli` 和 harness 安装在**同一个**环境里（在本仓库内或在路径 A
生成的项目里通常如此），两者都会争抢 console script 名字。后装的会赢，但
对用户而言行为是一致的：

- 如果 `agentseek-cli` 赢了，`agentseek_cli.standalone.app`
  （`contrib/agentseek-cli/src/agentseek_cli/standalone.py:24-32`）会检测到
  harness 可导入，并让位给 `agentseek.__main__.create_cli_app()`。
- 该函数启动 `BubFramework`，后者通过
  `contrib/agentseek-cli/pyproject.toml:20-21` 中的
  `[project.entry-points.bub]` 加载 `agentseek_cli.plugin:main`。
- plugin
  （`contrib/agentseek-cli/src/agentseek_cli/plugin.py:28-42`）把每个项目
  生命周期组挂到 framework app 上，并把 Bub 内置的 `run`（单条消息分发）
  覆盖为项目生命周期 CLI 的 `run`（本地启动项目）。

最终：单个 `agentseek …` 暴露两个表面的并集。每条命令属于哪个包详见
[CLI 参考](../reference/cli.zh.md)。

## 部署 / 扩展面

它们不是另外的入口，而是把路径 B 打包或扩展的方式。

### Docker Compose —— 在容器里运维 harness

`entrypoint.sh:5-26` 解析 `BUB_*`/`AGENTSEEK_*` 对、确保 home 与 project
目录存在，可选地把 `.agents/skills` 与 `.agents/mcp.json` 软链到运行时路径
（`entrypoint.sh:30-39`），最后 exec 工作区提供的 `startup.sh` 或
`agentseek gateway`（`entrypoint.sh:41-45`）。

Compose 就是把路径 B 的 harness 为运维场景打了包。当你需要一个挂载工作区
的长进程 gateway、又不想在 host 上管理 Python 环境时使用它。端到端流程见
[如何使用 Docker Compose 运行](../how-to/run-with-docker-compose.zh.md)。

### Contrib 包 —— 功能维度的扩展

每个 `contrib/agentseek-*/` 包都是一个可以安装在 harness 之上的 Python 发
行物。它们列在 [contrib/](https://github.com/ob-labs/agentseek/tree/main/contrib)
下，并通过 `pyproject.toml:27-46` 暴露为可选 extras。

这些是路径 B 的**运行时 plugin**：`agentseek-ag-ui`、`agentseek-langchain`、
`agentseek-tapestore-oceanbase`、`agentseek-observability`、
`agentseek-schedule-sqlalchemy`、`agentseek-contextseek`。它们扩展 harness，
不替代 harness。详见 [扩展模型](extension-model.zh.md)。

`agentseek-cli` 也在 `contrib/` 下，但它**不是**运行时 plugin —— 它是
路径 A 的独立项目生命周期 CLI，只是同时注册了一个 Bub plugin，以实现上面
所述的双模式行为。

## 为什么这样设计

- **每个包只做一件事。**路径 A 的用户不希望 harness 的依赖树出现在 laptop
  上；路径 B 的用户希望它在。把两者拆开能让安装尺寸合理、表面诚实。
- **同名是有意的。**用户从路径 A 走到路径 B（例如在生成项目里 `uv sync`），
  键入的命令仍然是 `agentseek …`。命令面变大，但命令名不变。
- **用 plugin 覆盖而不是硬编码。**harness 不会对 `agentseek-cli` 做特例。
  CLI plugin 就是一个普通的 Bub plugin，走的是别人也用的同一个
  `register_cli_commands` hook。

## 对用户的影响

- 如果你是**评估者（A1）**，对一个免费 model 走路径 B 是最短的可工作路径
  （[01 —— 通过 CLI 快速演示](../tutorials/01-quick-demo-cli.zh.md)）。
- 如果你是**应用开发者（A2）**，路径 A 生成项目，路径 B 在其中运行 harness
  （[02 —— 构建你的第一个 harness 应用](../tutorials/02-first-harness-app.zh.md)）。
- 如果你是**插件作者（A3）**，你住在路径 B。在 `agentseek` 与 `bub` 两边
  测试（见 [agentseek 与 Bub 的关系](bub-relationship.zh.md)），避免对 agentseek
  默认值意外耦合。
- 如果你是**运维（A4）**，路径 B 之上的 Compose 是起点；路径 B 的 CLI 是
  调试运行时的内循环工具。
- 如果你曾困惑「为什么 `agentseek …` 在两个环境里命令不同」——
  请看 [CLI 参考](../reference/cli.zh.md)，每条命令都标注了
  它属于哪个包。

## 相关

- 概览：[agentseek](../index.zh.md)
- 教程：[01 —— 通过 CLI 快速演示](../tutorials/01-quick-demo-cli.zh.md)、
  [02 —— 构建你的第一个 harness 应用](../tutorials/02-first-harness-app.zh.md)
- 操作指南：[如何在本地运行 agentseek](../how-to/run-locally.zh.md)、
  [如何使用 Docker Compose 运行](../how-to/run-with-docker-compose.zh.md)、
  [如何安装一个 plugin](../how-to/install-a-plugin.zh.md)
- 参考：[CLI 参考](../reference/cli.zh.md)、
  [包参考](../reference/packages.zh.md)、
  [Docker 参考](../reference/docker.zh.md)、
  [模板参考](../reference/templates.zh.md)
- 概念解释：[agentseek 是什么](what-agentseek-is.zh.md)、
  [agentseek 与 Bub 的关系](bub-relationship.zh.md)、
  [monorepo 中各样东西的位置](where-things-live.zh.md)
