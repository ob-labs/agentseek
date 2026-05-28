---
title: agentseek 是什么
type: explanation
audience: [A1, A2, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - blog/introducing-agentseek.md
  - pyproject.toml
  - src/agentseek/__main__.py
---

# agentseek 是什么

> **简而言之：** agentseek 是一个 **database-native 的 Agent Harness**，以 Python library
> 的形式分发，供你嵌入到自己的应用中。它打包了 [Bub](https://github.com/bubbuild/bub) 并
> 附带 project-local 默认值，让 runtime 数据 —— context、tool call、trace、task、feedback ——
> 从第一轮 turn 起就生活在同一个持久底层基座上。CLI 是一个 demo entry point，不是产品。

## 背景

大多数 agent 在 runtime 证明自己的价值，然后它们的数据就散落各处：session context 在一处，
tool call 在另一处，日志和 eval 产物在更多流水线里。在第一个消费者之后，再去查询、replay、
比较、评估或转化为训练材料都很昂贵 ——
见 [`../blog/introducing-agentseek.md`](../blog/introducing-agentseek.md)。

agentseek 从一个不同的假设出发：context、memory、task、tool call、trace、feedback 和评估
材料应当 **从一开始就共享一个持久底层基座**。这个基座天然就是一个数据库 —— 因此叫
"database-native"。harness 这种形态之所以存在，是因为大多数团队并不想发明一个 runtime；
他们想把自己的应用插到一个已经把 runtime 数据当作 first-class 负载的 runtime 上。

## 工作原理

三层叠在一起：

1. **Bub** 提供 kernel：一条 hook-first 的 turn 流水线、channel、一个 tape store、skill 和
   一个 plugin 模型。见 <https://github.com/bubbuild/bub>。
2. **agentseek** 把 Bub 打包并附带 project-local 默认值（`.agentseek/` runtime home、
   `AGENTSEEK_*` 环境 alias、位于 `.agentseek/agentseek-project` 的 install sandbox、
   `src/skills/` 下的捆绑 skill）—— 启动顺序见 `src/agentseek/__main__.py:18`，
   对 Bub 的依赖见 `pyproject.toml:18`。
3. **Contrib 包和你的应用** 坐在上面：存储后端、model 路由、observability、channel 适配器，
   以及那些实际想在 harness 上跑的应用代码。contrib monorepo 索引位于
   [`contrib/`](https://github.com/ob-labs/agentseek/tree/main/contrib)。

实践中，推荐路径是从你的项目依赖 `agentseek`（`pyproject.toml` 在
`[project] name = "agentseek"` 下把它声明为常规 distribution，`pyproject.toml:2`），
并让你的应用代码驱动 turn。CLI 恰好是一个启动同一个 framework 的薄 Typer app ——
见 `src/agentseek/__main__.py:52-69` —— 这就是为什么 CLI demo 是你应用将得到的东西的忠实预览。

## 为什么是这样

- **Harness，而非 framework。** harness 给你一个 runtime 底层基座，然后让开；framework
  规定你如何写你的 agent。agentseek 有意是前者，所以已经使用 LangChain、DeepAgents 或自有
  orchestration 的团队可以保留这些，只在下面采用 harness。`agentseek-langchain` contrib 包
  正是为这种情况存在的。
- **Database-native，而非 database-coupled。** harness 厘清的是 *写路径与语义*；实际的存储
  是部署关注。本地 SQLite 开箱即用；OceanBase / [seekdb](https://github.com/oceanbase/seekdb)
  是推荐的扩展路径，作为 contrib plugin 发布（`agentseek-tapestore-oceanbase`）。
- **CLI 作为 demo，而非产品。** 把 CLI 放在显眼位置会错误地传达项目是什么。CLI 是真实且被支持
  的，但它是评估者的入口，不是应用开发者用来构建的表面。见
  [`choosing-an-entry-point.md`](choosing-an-entry-point.md)。
- **下面是 Bub，上面是 agentseek。** agentseek 不去 fork 或替换 Bub，而是包裹它并提供
  opinionated 默认值。推理见 [`bub-relationship.md`](bub-relationship.md)。

## 对用户的影响

- 你被期望**把 agentseek 嵌入到一个应用中**。library 使用是主路径；
  见 [`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md)。
- 文档中任何看起来朴素的地方 —— 环境变量、文件布局、install sandbox 语义 —— 那种朴素是有意的。
  复杂性集中在 runtime 底层基座（Bub + tape）以及可选的 contrib 包中，而不在 agentseek 本身。
- 教程、操作指南和参考页面都假定你的项目有一个 `.agentseek/` 目录，并且 `AGENTSEEK_*` 变量
  驱动配置。为什么以及 alias 规则在 [`bub-relationship.md`](bub-relationship.md)；
  确切的表格在 [`../reference/environment.md`](../reference/environment.md)。

## 明确的非目标

agentseek **不**试图：

- 取代 LangChain、DeepAgents、LlamaIndex 或 AutoGen 这样的 agent framework。在旁边用它们；
  需要时通过 `agentseek-langchain` 把它们的 turn 路由到 harness 中。
- 成为一个通用 plugin 市场。plugin 模型是 Bub 的；更广泛的目录在 <https://hub.bub.build>。
  agentseek 只发布和维护
  [`contrib/`](https://github.com/ob-labs/agentseek/tree/main/contrib) 中列出的 contrib 包。
- 发布一个 UI。前端示例在 `examples/` 下，使用 CopilotKit、AG-UI 或你自选的 UI。
- 隐藏 Bub。需要不加修改的上游行为时，你随时可以直接落到 `bub …` ——
  见 [`bub-relationship.md`](bub-relationship.md)。
- 提供托管服务。部署由运维方拥有；harness 给你构建块，而不是 SaaS。

## 相关

- 教程：[`../tutorials/02-first-harness-app.md`](../tutorials/02-first-harness-app.md)
- 概念解释：[`bub-relationship.md`](bub-relationship.md),
  [`choosing-an-entry-point.md`](choosing-an-entry-point.md)
- 参考：[`../reference/environment.md`](../reference/environment.md),
  [`../reference/packages.md`](../reference/packages.md)
- 外部：[Introducing agentseek (blog)](../blog/introducing-agentseek.md),
  [Bub repository](https://github.com/bubbuild/bub),
  [Tape Systems](https://tape.systems/)
