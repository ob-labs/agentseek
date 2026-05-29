---
title: agentseek 文档
type: explanation
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-05-29
sources:
  - README.md
  - src/agentseek/__main__.py
  - contrib/agentseek-cli/pyproject.toml
  - pyproject.toml
---

# agentseek

agentseek 是一个 database-native 的 Agent Harness。context、tool call、trace 与
feedback 从第一轮 turn 起，就落到同一个持久、可查询的底层基座上 —— 无论你是在
终端里驱动它，还是把它嵌入到自己的应用代码中。

## 两条同为一等的入口

agentseek 在 PyPI 上以**两个互补的包**形式提供，按职责拆分：`agentseek-cli`
负责**项目生命周期**（脚手架、run、build、deploy），`agentseek` 是 **harness**
本身（chat、gateway、运行时）。按你正在做的事情来选，不要去判断哪一种「更
正式」。

| 你想做的事 | 起步方式 | 安装后 `agentseek` 提供的命令 |
| --- | --- | --- |
| **生成项目**，再从 harness 外部 run / build / deploy 它 | `uv tool install agentseek-cli` | 项目生命周期命令：`create`、`run`、`build`、`deploy`、`api`、`ctx`、`skills` |
| **运行 harness 本体** —— 跟模型对话、驱动 channel、启动 gateway | 克隆仓库 + `uv sync` | Harness 运行时命令：`chat`、`run`、`gateway`、`install`、`update`、… |

两条路径最后都会提供一个名为 `agentseek` 的命令。共用同一个名字是有意的：
项目生命周期 CLI 生成 harness 应用，而生成出来的 harness 应用最终运行的是
同一个框架。完整的取舍与"为什么拆成两个包"见
[`explanation/choosing-an-entry-point.md`](explanation/choosing-an-entry-point.md)。

### 路径 A —— 从 PyPI 安装项目生命周期 CLI

`agentseek-cli` 是**项目生命周期 CLI**：一个自包含的 Typer 应用，依赖树很小，
负责脚手架与项目生命周期命令。当你只需要生成项目、构建镜像、调用 `run /
build / deploy / api / ctx / skills`（开发机或 CI 场景），这就是该装的那个。

```bash
# 把 `agentseek` 可执行入口装进 uv 管理的隔离 venv。
uv tool install agentseek-cli
agentseek --help            # create / run / build / deploy / api / ctx / skills
agentseek create bub --template default --no-input
cd my_bub_agent
```

生成出来的项目会把 `agentseek`（harness 库）以及该模板需要的 contrib 包写进
依赖。进入项目目录后 `uv sync` 会通过该项目自己的 `pyproject.toml` 解析整套
harness —— 包括 git source 依赖。这一步把你从路径 A 自然过渡到路径 B。

教程：[`tutorials/02-first-harness-app.md`](tutorials/02-first-harness-app.md)。
参考：[`reference/cli.md`](reference/cli.md)。

### 路径 B —— 克隆仓库，运行 harness

**harness**（`agentseek`）依赖少数几个只能通过 `[tool.uv.sources]` 解析的包
（典型是 `bub-feishu`、`bub-mcp`，以及 `contrib/` 下的 workspace 包）。PyPI 的
metadata 无法携带 git source，所以直接执行 `pip install agentseek` 或
`uv tool install agentseek` 都会因为找不到这些依赖而失败。可靠的路径是使用
一个把这些 source 写在里面的项目 —— 要么是本仓库，要么是路径 A 生成出来的
项目。

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync                     # 解析 bub、bub-feishu、bub-mcp 以及 contrib 包
export AGENTSEEK_MODEL=openai:gpt-4o-mini
export AGENTSEEK_API_KEY=sk-...
uv run agentseek chat       # harness CLI：基于 Bub 的 chat REPL
```

教程：[`tutorials/01-quick-demo-cli.md`](tutorials/01-quick-demo-cli.md)。
参考：[`reference/cli.md`](reference/cli.md)。

### 怎么选

- **第一次试用** —— 用路径 B 跑一个免费 model，是看到完整 turn 跑通最快的方式。
- **基于 harness 构建自己的应用** —— 用路径 A 生成项目，然后在生成出来的项目里
  `uv sync`（这会把你带到属于你自己的路径 B 树里）。
- **运维一个 workspace** —— 在仓库或生成项目里走路径 B，通常配合 Docker Compose，
  见 [`how-to/run-with-docker-compose.md`](how-to/run-with-docker-compose.md)。
- **只跑 `build` / `deploy` 的 CI** —— 路径 A 单独就够用，它不会拉 harness 运行时。

## 按象限阅读

文档遵循 [Diátaxis 框架](https://diataxis.fr/)。每个页面都只属于以下四个分组之一。
选择与你当前正在做的事情相匹配的那一个。

| 象限 | 何时使用 | 索引 |
| --- | --- | --- |
| **教程** —— 边做边学 | 你是新手，希望通过一次有人带的运行得到一个可工作的环境。 | [`tutorials/index.md`](tutorials/index.md) |
| **操作指南** —— 解决特定任务 | 你已经熟悉系统，需要到达某个结果的最短路径。 | [`how-to/index.md`](how-to/index.md) |
| **参考** —— 查询确切事实 | 你需要环境变量、CLI flags、文件路径或 extras 的权威清单。 | [`reference/index.md`](reference/index.md) |
| **概念解释** —— 理解设计 | 你想知道*为什么* agentseek 是这个样子，以及它如何与 Bub 共存。 | [`explanation/index.md`](explanation/index.md) |

## 项目的目录结构

agentseek 是一个 monorepo。**harness** 位于 `src/agentseek/`（PyPI 包名
`agentseek`）；**项目生命周期 CLI** 位于 `contrib/agentseek-cli/`（PyPI 包名
`agentseek-cli`）；更大的集成位于 `contrib/`，并拥有各自的 README；可运行的
端到端示例位于 `examples/`。带注释的目录地图见
[`explanation/where-things-live.md`](explanation/where-things-live.md)。

外部参考：

- 上游 runtime：<https://github.com/bubbuild/bub>
- 更广泛的生态目录：<https://hub.bub.build>
- 项目背景：[`blog/introducing-agentseek.md`](blog/introducing-agentseek.md)
