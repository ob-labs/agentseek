---
title: 概念解释 —— 理解 agentseek
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - docs/index.md
  - docs/blog/introducing-agentseek.md
  - src/agentseek/env.py
  - pyproject.toml
---

# 概念解释

> **简而言之：** 这些页面告诉你 *为什么* agentseek 是现在的样子 —— 它是什么、与 Bub 有什么关系、
> 什么数据流经 runtime，以及如何在提供的 entry point 和 extension point 之间做出选择。

概念解释页面是讨论性质的。它们不会一步步带你完成任务（那是
[教程](../tutorials/index.zh.md) 的职责），也不是权威的事实清单（需要确切数值时
请使用 [参考](../reference/index.zh.md)）。当某个操作指南看起来过于机械、你想
知道为什么是这种形态时，就来读它们。

## 本组中的页面

| 页面 | 何时阅读 |
| --- | --- |
| [agentseek 是什么](what-agentseek-is.zh.md) | 你正在评估这个项目，需要一页式的概览：database-native harness、按职责拆分的两个包（`agentseek-cli` 与 `agentseek`），以及明确的非目标。 |
| [agentseek 与 Bub 的关系](bub-relationship.zh.md) | 你想了解 `agentseek` 和 `bub` 如何分工、alias 模型为什么存在，以及何时直接落到 `bub`。 |
| [agentseek 与 LangChain 的关系](langchain-relationship.zh.md) | 你已经在用 LangChain / LangGraph / DeepAgents，想了解 AgentSeek 如何补齐这个生态——它加了什么、不替代什么，以及该选哪个模板。 |
| [运行时数据模型](runtime-data-model.zh.md) | 你即将编写一个 plugin、skill 或 tape 消费者，需要一个关于 tape、skill、MCP、plugin 和 channel 的心智模型。 |
| [扩展模型](extension-model.zh.md) | 你想扩展 runtime，需要在打开对应操作指南之前，在 instructions、skill、plugin、MCP 和 contrib 包之间做出决策。 |
| [选择一个入口](choosing-an-entry-point.zh.md) | 你正在路径 A（`agentseek-cli`）、路径 B（`uv sync` 后的 `agentseek`）、Docker Compose，或 contrib 包之间做选择。 |
| [monorepo 中各样东西的位置](where-things-live.zh.md) | 你第一次在 monorepo 中导航，希望得到 `src/`、`contrib/`、`examples/`、`templates/`、`skills/`、`references/` 和 `docs/` 的带注释地图。 |

## 这里不涉及的内容

- 让某个东西跑起来的分步说明 —— 参见
  [教程](../tutorials/index.zh.md) 和
  [操作指南](../how-to/index.zh.md)。
- 环境变量、CLI flags、文件路径、可选 extras 或模板的详尽清单 —— 参见
  [参考](../reference/index.zh.md)。
- contrib 包的安装、配置和运行行为 —— 每个 contrib 包都有自己的 README
  （参见 [contrib 包](https://github.com/ob-labs/agentseek/tree/main/contrib)）。
  概念解释页面只链接出去，不重复。

## 推荐阅读顺序

1. [agentseek 是什么](what-agentseek-is.zh.md) 了解定位。
2. [agentseek 与 Bub 的关系](bub-relationship.zh.md) 了解内核分层。
3. [agentseek 与 LangChain 的关系](langchain-relationship.zh.md) 如果你来自 LangChain 生态。
4. [运行时数据模型](runtime-data-model.zh.md) 了解底层基座。
5. 当你准备开始构建时，阅读 [扩展模型](extension-model.zh.md) 和
   [选择一个入口](choosing-an-entry-point.zh.md)。
6. [monorepo 中各样东西的位置](where-things-live.zh.md) 作为你会反复回来查阅的参考地图。
