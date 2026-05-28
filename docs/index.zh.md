---
title: agentseek 文档
type: explanation
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - src/agentseek/env.py
  - pyproject.toml
---

# agentseek

agentseek 是一个 **database-native 的 Agent Harness**：一个与 Bub 兼容的运行时 distribution，
你可以**将它嵌入到自己的应用中**，让 context、tool calls、traces 和 feedback 从第一轮对话开始就
落到一个持久、可查询的底层基座上。

harness/library 形态是这套文档的主线。`agentseek` CLI 的存在是为了在五分钟内向你证明这个项目能在
你机器上跑起来；它不是产品形态。

## 从这里开始

- **试用 CLI demo（5 分钟）** —— clone、安装，并对一个免费模型跑一轮对话。
  参见 [`tutorials/01-quick-demo-cli.md`](tutorials/01-quick-demo-cli.md)。
- **嵌入到你的应用中（15 分钟）** —— 从模板脚手架出一个项目，把一轮对话路由到你自己的代码里，
  同时让 harness 掌管状态。
  参见 [`tutorials/02-first-harness-app.md`](tutorials/02-first-harness-app.md)。

如果你不确定自己属于哪一类，先阅读
[`explanation/what-agentseek-is.md`](explanation/what-agentseek-is.md)。

## 按象限阅读

文档遵循 [Diátaxis 框架](https://diataxis.fr/)。每个页面都只属于以下四个分组之一。选择与你
当前正在做的事情相匹配的那一个。

| 象限 | 何时使用 | 索引 |
| --- | --- | --- |
| **教程** —— 边做边学 | 你是新手，希望通过一次有人带的运行得到一个可工作的环境。 | [`tutorials/index.md`](tutorials/index.md) |
| **操作指南** —— 解决特定任务 | 你已经熟悉系统，需要到达某个结果的最短路径。 | [`how-to/index.md`](how-to/index.md) |
| **参考** —— 查询确切事实 | 你需要环境变量、CLI flags、文件路径或 extras 的权威清单。 | [`reference/index.md`](reference/index.md) |
| **概念解释** —— 理解设计 | 你想知道 *为什么* agentseek 是这个样子，以及它如何与 Bub 共存。 | [`explanation/index.md`](explanation/index.md) |

## 项目的目录结构

agentseek 是一个 monorepo。核心 distribution 位于 `src/agentseek/`；更大的集成位于 `contrib/`，
并拥有各自的 README；可运行的端到端示例位于 `examples/`。带注释的目录地图见
[`explanation/where-things-live.md`](explanation/where-things-live.md)。

外部参考：

- 上游 runtime：<https://github.com/bubbuild/bub>
- 更广泛的生态目录：<https://hub.bub.build>
- 项目背景：[`blog/introducing-agentseek.md`](blog/introducing-agentseek.md)
