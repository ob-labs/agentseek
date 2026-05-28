---
title: 概念解释 —— 理解 agentseek
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - docs/blog/introducing-agentseek.md
  - src/agentseek/env.py
  - pyproject.toml
---

# 概念解释

> **简而言之：** 这些页面告诉你 *为什么* agentseek 是现在的样子 —— 它是什么、与 Bub 有什么关系、
> 什么数据流经 runtime，以及如何在提供的 entry point 和 extension point 之间做出选择。

概念解释页面是讨论性质的。它们不会一步步带你完成任务（那是
[`../tutorials/index.md`](../tutorials/index.md) 的职责），也不是权威的事实清单（需要确切数值时
请使用 [`../reference/index.md`](../reference/index.md)）。当某个操作指南看起来过于机械、你想
知道为什么是这种形态时，就来读它们。

## 本组中的页面

| 页面 | 何时阅读 |
| --- | --- |
| [`what-agentseek-is.md`](what-agentseek-is.md) | 你正在评估这个项目，需要一页式的概览：database-native harness、harness/library 是主线、CLI 是 demo、以及明确的非目标。 |
| [`bub-relationship.md`](bub-relationship.md) | 你想了解 `agentseek` 和 `bub` 如何分工、alias 模型为什么存在，以及何时直接落到 `bub`。 |
| [`runtime-data-model.md`](runtime-data-model.md) | 你即将编写一个 plugin、skill 或 tape 消费者，需要一个关于 tape、skill、MCP、plugin 和 channel 的心智模型。 |
| [`extension-model.md`](extension-model.md) | 你想扩展 runtime，需要在打开对应操作指南之前，在 instructions、skill、plugin、MCP 和 contrib 包之间做出决策。 |
| [`choosing-an-entry-point.md`](choosing-an-entry-point.md) | 你正在 library 嵌入、运行 CLI、用 Docker Compose 部署、或引入 contrib 包之间做选择。 |
| [`where-things-live.md`](where-things-live.md) | 你第一次在 monorepo 中导航，希望得到 `src/`、`contrib/`、`examples/`、`templates/`、`skills/`、`references/` 和 `docs/` 的带注释地图。 |

## 这里不涉及的内容

- 让某个东西跑起来的分步说明 —— 参见
  [`../tutorials/index.md`](../tutorials/index.md) 和
  [`../how-to/index.md`](../how-to/index.md)。
- 环境变量、CLI flags、文件路径、可选 extras 或模板的详尽清单 —— 参见
  [`../reference/index.md`](../reference/index.md)。
- contrib 包的安装、配置和运行行为 —— 每个 contrib 包都有自己的 README
  （参见 [`contrib/`](https://github.com/ob-labs/agentseek/tree/main/contrib)）。
  概念解释页面只链接出去，不重复。
- 中文翻译 —— 翻译会在英文结构定稿后再跟进。

## 推荐阅读顺序

1. [`what-agentseek-is.md`](what-agentseek-is.md) 了解定位。
2. [`bub-relationship.md`](bub-relationship.md) 了解分层。
3. [`runtime-data-model.md`](runtime-data-model.md) 了解底层基座。
4. 当你准备开始构建时，阅读 [`extension-model.md`](extension-model.md) 和
   [`choosing-an-entry-point.md`](choosing-an-entry-point.md)。
5. [`where-things-live.md`](where-things-live.md) 作为你会反复回来查阅的参考地图。
