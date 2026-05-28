---
title: 选择一个 entry point
type: explanation
audience: [A1, A2, A4, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli.py
  - entrypoint.sh
  - contrib/README.md
  - examples/README.md
---

# 选择一个 entry point

> **简而言之：** agentseek 有四个 entry point —— **library**（嵌入到你的应用中）、
> **`agentseek` CLI**、**Docker Compose**，以及 **contrib 包**。对于应用开发者而言，
> 推荐的路径是 library；其他一切都是同一个 framework 上的封装。

## 背景

人们以不同方式接触 agentseek。评估者想要一条命令搞定的 demo。应用开发者希望把 harness 放进自己
已经拥有的服务里。运维人员想要一个可以挂载 workspace 进去的容器。Plugin 作者想要选一个现成的
contrib 包或脚手架出一个新的。这四个 entry point 的存在，让每条流程都有一个明确的起点 ——
但很容易把 demo entry 误以为是产品。本页要把这一点说清楚。

## 工作原理

### Library —— 推荐路径

把 `agentseek` 作为普通 Python distribution 依赖
（`pyproject.toml:2` 声明了项目名），然后从你自己的代码驱动 framework。启动 framework 正是
`src/agentseek/__main__.py:52-69` 为 CLI 所做的：

1. 调用 `apply_agentseek_env_aliases()` 和 `apply_agentseek_cli_overrides()`（如果你不需要
   CLI override，可以跳过后者）。
2. 构造 `BubFramework(config_file=agentseek_config_file())`。
3. 调用 `load_hooks()`，并通过任意你需要的 channel 路由 turn。

这就是教程和操作指南所基于的表面。Library 形态给你：

- 对一轮 turn 如何分发的完全控制（你的应用选择 channel、lifecycle、请求形态）。
- 保留现有 framework 代码（LangChain、DeepAgents、你自己的 orchestrator）的能力，
  并通过 `agentseek-langchain` 路由 model turn，同时让 harness 掌管状态。
- 与所有其他 entry point 一致的 tape、plugin 和 MCP 行为 —— 因为所有其他 entry point 启动
  的是同一个 framework。

`templates/` 下的项目模板（见 [`../reference/templates.md`](../reference/templates.md)）
的存在是为了跳过模板代码。端到端应用教程是
[`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md)。

### CLI —— 快速 demo

`agentseek …` 是一个由 `BubFramework.create_cli_app()` 产出的 Typer app
（`src/agentseek/__main__.py:52-66`）。它暴露了 Bub 的内置命令加上 contrib 子命令，
并带有 `src/agentseek/cli.py:74-152` 的三处刻意 override：

- onboarding banner 读作 `AGENTSEEK`，
- `chat` 启用 lifecycle channel，以便 MCP 和同类启动，
- `install` 使用带 agentseek 命名的 plugin sandbox。

在以下场景使用 CLI：

- **评估** 项目。在五分钟内对一个免费模型跑 `agentseek chat` 是
  [`../tutorials/01-quick-demo-cli.md`](../tutorials/01-quick-demo-cli.md) 的全部要点。
- **运维** 一个 workspace。`agentseek run`、`agentseek gateway`、`agentseek install` 以及
  contrib 提供的 lifecycle 命令（`agentseek create`、`build`、`deploy`、`api`、
  `ctx`、`skills`）都是真正的运维表面；目录位于
  [`../reference/cli.md`](../reference/cli.md)。
- **调试** harness 行为，对照一个 Bub Hub 示例。

CLI **不是**你围绕来构建应用的地方。任何你打算放进 shell 流水线的东西，通常都可以通过依赖
library 并直接调用 framework 来表达得更清晰。

### Docker Compose —— 运维路径

`entrypoint.sh:5-26` 解析 `BUB_*`/`AGENTSEEK_*` 配对、导出两者、确保 home 和 project 目录
存在，可选地把 `.agents/skills` 和 `.agents/mcp.json` symlink 到 runtime 路径
（`entrypoint.sh:30-39`），最后 exec 一个由 workspace 提供的 `startup.sh` 或
`agentseek gateway`（`entrypoint.sh:41-45`）。

当你想要一个 **mounted workspace** 加上一个长期运行的 gateway，又不想在宿主机上管理 Python
环境时使用 Compose。默认会把当前 repo 挂载到 `/workspace`，让 `.agents/skills` 和
`.agents/mcp.json` 可用，并把 runtime 状态持久化到 workspace 下的 `.agentseek/`
（面向用户的命令参见 [`README.md`](https://github.com/ob-labs/agentseek/blob/main/README.md)
的 Quick Start 部分；
[`../how-to/run-with-docker-compose.md`](../how-to/run-with-docker-compose.md) 是权威的
分步指南）。

底层上 Compose 仍是 library 形态 —— `entrypoint.sh` 只是在启动 `agentseek gateway` 之前
设置环境和挂载。如果你有一个自定义服务，可以在 workspace 里放一个 `startup.sh`，entrypoint
会改为 exec 它。

### Contrib 包 —— 面向功能的 entry point

每个 `contrib/agentseek-*/` 包都是一个可以装在 core 之上的 Python distribution。
它们罗列在 [`contrib/`](https://github.com/ob-labs/agentseek/tree/main/contrib) 中，并在
`pyproject.toml:27-46` 下作为可选 extras 暴露。其中本身就充当 entry point 的两个是：

- **`agentseek-cli`** —— 添加项目生命周期命令（`create / run / build / deploy / api / ctx
  / skills`）。你可以把它作为 extra 安装（`uv sync --extra cli`），把这些命令折叠进
  `agentseek …`；或者当你不希望它接触主环境时，通过 `uvx agentseek-cli` 独立运行。
- **`agentseek-ag-ui`** —— 为 `agentseek gateway` 添加 AG-UI SSE channel，这是连接
  CopilotKit 风格前端的桥梁。端到端形态见
  [`examples/ag-ui`](https://github.com/ob-labs/agentseek/tree/main/examples/ag-ui) 示例。

其他 contrib 包（`agentseek-langchain`、`agentseek-tapestore-oceanbase`、
`agentseek-observability`、`agentseek-schedule-sqlalchemy`、`agentseek-contextseek`）
是 runtime plugin 而不是 entry point；它们扩展 library、CLI、Compose 路径共享的同一个
framework。见 [`extension-model.md`](extension-model.md)。

## 为什么是这样

- **Library 优先。** harness 的本意是承载应用代码。把 library 放在中心位置可以让所有其他
  entry point 保持诚实：它们必须可以在同一个 framework 之上实现，事实上也确实如此。
- **CLI 作为存活证明。** 五分钟的 demo 是向陌生人的机器展示项目能工作的最廉价方式。把 CLI 推到
  产品位置会把应用开发者推向 shell 胶水，远离 library。
- **Compose 服务于运维。** 一条 `make compose-up` 配合 mounted workspace，是让别人的 checkout
  以相同默认值跑起来的最快方式。entrypoint 刻意只做：设环境、确保路径、exec —— 没有魔法。
- **Contrib 作为可选的功能表面。** 每个 contrib 包拥有自己的依赖树和文档；core distribution
  保持小巧。`pyproject.toml` 中的 extras 是项目对外宣告这个表面而不强加给所有人的方式。

## 对用户的影响

- 如果你是**应用开发者（A2）**，从 library 教程开始
  （[`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md)）。
  CLI demo（[`../tutorials/01-quick-demo-cli.md`](../tutorials/01-quick-demo-cli.md)）
  是在你下定决心使用 library 形态前的一次性 sanity check。
- 如果你是**评估者（A1）**，CLI demo 是正确的起点，library 教程是可选项。
- 如果你是**运维（A4）**，Compose 是正确的起点；CLI 是你戳 runtime 的内循环工具。
- 如果你是**plugin 作者（A3）**，你把 plugin 嵌入到所有四个 entry point 共享的同一个 Python
  环境中。在 `agentseek` 和 `bub` 下都测试
  （见 [`bub-relationship.md`](bub-relationship.md)），以捕捉对 agentseek 默认值的无意耦合。
- 任何你混用路径的地方 —— 例如在开发时用 CLI、在 staging 用 Compose —— 底层 framework 是相同的，
  但环境变量解析略有不同。完整表格在
  [`../reference/environment.md`](../reference/environment.md)。

## 相关

- 教程：[`../tutorials/01-quick-demo-cli.md`](../tutorials/01-quick-demo-cli.md),
  [`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md)
- 操作指南：[`../how-to/run-locally.md`](../how-to/run-locally.md),
  [`../how-to/run-with-docker-compose.md`](../how-to/run-with-docker-compose.md),
  [`../how-to/install-a-plugin.md`](../how-to/install-a-plugin.md)
- 参考：[`../reference/cli.md`](../reference/cli.md),
  [`../reference/packages.md`](../reference/packages.md),
  [`../reference/docker.md`](../reference/docker.md),
  [`../reference/templates.md`](../reference/templates.md)
- 概念解释：[`what-agentseek-is.md`](what-agentseek-is.md),
  [`bub-relationship.md`](bub-relationship.md),
  [`where-things-live.md`](where-things-live.md)
