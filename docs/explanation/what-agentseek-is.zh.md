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

> **简而言之：** AgentSeek 是一个帮你把 agent 送上生产的**套件**。
> 它包含 agentseek-cli（项目脚手架）、agentseek-api（Agent Protocol 服务）、
> ContextSeek（语义上下文层）和 langchain-oceanbase（数据底座）。AgentSeek 开放
> 接入任何智能体框架——内置 Bub，当前版本开箱即用地支持 LangChain。套件构建在
> database-native 的 harness 之上——运行时数据从第一轮 turn 起就生活在持久可查的
> 数据库里。

> **来自 LangChain？** 建议先读
> [agentseek 与 LangChain 的关系](langchain-relationship.zh.md)——它讲清楚
> AgentSeek 为 LangChain 生态加了什么以及该选哪个模板。

## 背景

大多数 agent 在 runtime 证明自己的价值，然后它们的数据就散落各处：session context 在一处，
tool call 在另一处，日志和 eval 产物在更多流水线里。在第一个消费者之后，再去查询、replay、
比较、评估或转化为训练材料都很昂贵 ——
见 [认识 agentseek](../blog/introducing-agentseek.zh.md)。

agentseek 从一个不同的假设出发：context、memory、task、tool call、trace、feedback 和评估
材料应当 **从一开始就共享一个持久底层基座**。这个基座天然就是一个数据库 —— 因此叫
"database-native"。harness 这种形态之所以存在，是因为大多数团队并不想发明一个 runtime；
他们想把自己的应用插到一个已经把 runtime 数据当作 first-class 负载的 runtime 上。

## 工作原理

四层叠在一起：

1. **Bub** 提供 kernel：一条 hook-first 的 turn 流水线、channel、一个 tape store、skill 和
   一个 plugin 模型。见 <https://github.com/bubbuild/bub>。
2. **`agentseek`（harness）** 运行在 Bub 之上。它拥有运行时 CLI
   （`chat`、`run`、`gateway`、`install`、`update`、……）、可嵌入的 library
   表面，以及 project-local 默认值（`.agentseek/` runtime home、`AGENTSEEK_*`
   到 `BUB_*` 的 alias、位于 `.agentseek/agentseek-project` 的 install sandbox、
   `src/skills/` 下的捆绑 skill）。启动序列见 `src/agentseek/__main__.py:52-69`，
   对 Bub 的依赖见 `pyproject.toml:18-25`。
3. **`agentseek-cli`（项目生命周期 CLI）** 是第二个 PyPI 包。它负责脚手架与
   生命周期命令（`create / run / build / deploy / api / ctx / skills`）。
   单独安装时依赖树小、适合 laptop 或 CI；与 harness 共存时，它会作为 Bub plugin
   合并进同一个 `agentseek` 命令面。详见
   [选择一个入口](choosing-an-entry-point.zh.md)。
4. **Contrib 包和你的应用** 坐在上面：存储后端、model 路由、observability、channel 适配器，
   以及那些实际想在 harness 上跑的应用代码。contrib monorepo 索引位于
   [contrib/](https://github.com/ob-labs/agentseek/tree/main/contrib)。

实践中，大多数应用团队会在自己的项目里依赖 `agentseek`，并让应用代码驱动 turn。
评估者和运维常先接触到 `agentseek` 命令；但这个命令背后既可能是路径 A 的
`agentseek-cli`，也可能是路径 B 的 harness，或者是在同一环境里合并后的命令面。
命令归属与合并机制见 [选择一个入口](choosing-an-entry-point.zh.md)。

## 为什么是这样

- **Harness，而非 framework。** harness 给你一个 runtime 底层基座，然后让开；framework
  规定你如何写你的 agent。agentseek 有意是前者，所以已经使用 LangChain、DeepAgents 或自有
  orchestration 的团队可以保留这些，只在下面采用 harness。`agentseek-langchain` contrib 包
  正是为这种情况存在的。
- **Database-native，而非 database-coupled。** harness 厘清的是 *写路径与语义*；实际的存储
  是部署关注。本地 SQLite 开箱即用；OceanBase / [seekdb](https://github.com/oceanbase/seekdb)
  是推荐的扩展路径，作为 contrib plugin 发布（`agentseek-tapestore-oceanbase`）。
- **两个包，各做一件事。** `agentseek-cli` 让只需要脚手架与生命周期命令的团队不必
  把 harness 的完整依赖树装到 laptop 或 CI 上；`agentseek` 则让 harness 保持为
  一个正常的 Python 包，供你嵌入自己的应用。取舍与“同名命令、共存时命令面合并”
  的机制见 [选择一个入口](choosing-an-entry-point.zh.md)。
- **下面是 Bub，上面是 agentseek。** agentseek 不去 fork 或替换 Bub，而是包裹它并提供
  opinionated 默认值。推理见 [agentseek 与 Bub 的关系](bub-relationship.zh.md)。

## 对用户的影响

- 按工作选择包。`agentseek-cli` 适合在 host 上不安装 harness runtime 的情况下做
  脚手架、构建和部署；`agentseek` 则是你在本仓库 `uv sync` 之后，或在生成项目里
  `uv sync` 之后真正运行的 harness。
- 大多数评估者会从路径 B 和 `agentseek chat` 开始
  （[01 —— 通过 CLI 快速演示](../tutorials/01-quick-demo-cli.zh.md)）。
  大多数应用团队则会先用路径 A 生成项目，再在生成项目里进入路径 B
  （[02 —— 构建你的第一个 harness 应用](../tutorials/02-first-harness-app.zh.md)）。
- 文档中任何看起来朴素的地方 —— 环境变量、文件布局、install sandbox 语义 —— 那种朴素是有意的。
  复杂性集中在 runtime 底层基座（Bub + tape）以及可选的 contrib 包中，而不在 agentseek 本身。
- 教程、操作指南和参考页面都假定你的项目有一个 `.agentseek/` 目录，并且 `AGENTSEEK_*` 变量
  驱动配置。为什么以及 alias 规则在 [agentseek 与 Bub 的关系](bub-relationship.zh.md)；
  确切的表格在 [环境变量参考](../reference/environment.zh.md)。

## 明确的非目标

agentseek **不**试图：

- 取代智能体框架。AgentSeek 是 harness，不是框架。在旁边用它们；
  需要时通过 `agentseek-langchain` 把它们的 turn 路由到 harness 中。
- 成为一个通用 plugin 市场。plugin 模型是 Bub 的；更广泛的目录在 <https://hub.bub.build>。
  agentseek 只发布和维护
  [contrib/](https://github.com/ob-labs/agentseek/tree/main/contrib) 中列出的 contrib 包。
- 发布一个 UI。前端示例在 `examples/` 下，使用 CopilotKit、AG-UI 或你自选的 UI。
- 隐藏 Bub。需要不加修改的上游行为时，你随时可以直接落到 `bub …` ——
  见 [agentseek 与 Bub 的关系](bub-relationship.zh.md)。
- 提供托管服务。部署由运维方拥有；harness 给你构建块，而不是 SaaS。

## 相关

- 教程：[02 —— 构建你的第一个 harness 应用](../tutorials/02-first-harness-app.zh.md)
- 概念解释：[agentseek 与 Bub 的关系](bub-relationship.zh.md),
  [选择一个入口](choosing-an-entry-point.zh.md)
- 参考：[环境变量参考](../reference/environment.zh.md),
  [包参考](../reference/packages.zh.md)
- 外部：[认识 agentseek（博客）](../blog/introducing-agentseek.zh.md),
  [Bub repository](https://github.com/bubbuild/bub),
  [Tape Systems](https://tape.systems/)
