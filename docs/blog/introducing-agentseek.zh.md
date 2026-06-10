# 认识 agentseek

**2026-05-28**

agentseek 是构建在 [Bub](https://github.com/bubbuild/bub) 之上的 **数据库原生 Agent
Harness**。它为上游 kernel 套上了有主张的工作区默认值、项目命令，以及一组
精简的 contrib 插件，让运行时数据 —— context、tool call、trace、评测物料 —— 从一开始
就能落在同一个可查询的存储底座上。

这篇文章解释项目的来历、它在 2026-05 实际是什么样子，以及为什么我们坚持把它定位为
harness 而非 framework。

## 从 bubseek 到 agentseek

我们最早以 **bubseek** 的名字发布探索性的工作。方向 —— 在 **seekdb** 之上做内生可
观测和 insight 风格的 agent —— 在 OceanBase 工程博客上有完整阐述：
[Intrinsic Observability: Build an Insight Agent on seekdb](https://en.oceanbase.com/blog/26947000576)。

边界逐渐清晰之后，两件事变得明显：

- 真正有趣的对象不是某个垂直 agent，而是支撑每一次 agent 运行的 **运行时底座**。
- 这个底座的通用发行版，只要做得足够小、允许各家接入自己的模型、通道和存储，价值
  远不止 insight 场景。

于是我们 **改名为 agentseek**，把项目聚焦到 harness 这一层 —— 决定数据存在哪里、
插件如何加载、工作区长什么样的那一层。垂直部分要么沉到上游 Bub，要么进了 contrib
包，要么独立成项目。

## agentseek 今天的样子

agentseek 今天是一个顶层 Python 包，加上一组 uv workspace 内的 contrib 包。

**harness 发行版**（`agentseek`）拥有 runtime、项目命令和公开 CLI：

- 启动时将 `AGENTSEEK_*` 环境变量映射到 Bub 的 `BUB_*` 名字。
- Bub 内置命令被替换为 AgentSeek 自己的实现（品牌化 onboard、lifecycle-aware chat、plugin 分组）。
- 项目生命周期命令：`create / run / build / deploy / api / ctx / skills`。
- 单个 `BubFramework` 启动并作为 runtime。

捆绑的硬依赖和可通过 `agentseek plugin install` 安装的可选插件列在
[包参考](../reference/packages.zh.md) 中。整个目录布局 —— `src/`、`contrib/`、
`examples/`、`templates/`、`skills/`、`references/`、`docs/` ——
见 [文件存放位置](../explanation/where-things-live.zh.md)。

命令按使用场景分组：`agentseek create/run/build/deploy` 管理项目，
`agentseek chat/turn/gateway` 运行 runtime，`agentseek plugin/ctx/skills/api` 连接扩展和服务。
详见[命令概览](../explanation/cli-surface.zh.md)。

## "数据库原生"到底是什么意思

很长一段时间里，数据库主要装 **业务结果**：订单、用户、内容、索引、分析表。Agent
运行的产物则散落在数据库 **之外**：session context 在一个地方，tool call 和 trace
在另一个地方，日志和评测物料又在更多管道里。常见形式包括 JSONL 本地流、Markdown
笔记，偶尔有 SQLite sidecar。

这套做法处理一次性任务还可以。一旦同样的数据要喂给 **调试、回放、对比、评测、训练**，
成本就上去了 —— 每一个新消费方都要重新跑一遍 ingestion 管道。

agentseek 的赌注是：运行时产物一开始就应该落在 **同一个可持久的层** 上。具体来说，
这一层就是 Bub 的 **tape**：一条 append-only 的事实流，按顺序记录输入、模型调用、
工具调用与结果、anchor、以及派生视图。模型本身在 [Tape Systems](https://tape.systems/)
有完整描述，作为运行时数据形态则在
[运行时数据模型](../explanation/runtime-data-model.zh.md) 里说明。

两个推论自然落下来，我们也据此组织整个项目：

1. **运行时数据天然可查。** "这一类 tool call 随时间的分布"、"这次失败前后的状态"、
   "触发过 fallback 的轨迹" —— 全部都是对 tape store 的 SQL（可选向量）查询，不再
   需要额外的索引层。
2. **Context、observability、下游再消费共用同一个底座。** harness 负责把 **写入
   路径和语义** 说清楚；具体落到本地 SQLite、OceanBase 还是
   [seekdb](https://github.com/oceanbase/seekdb)，是部署和 contrib 的事情。
   OceanBase 后端以 `agentseek-tapestore-oceanbase` 名义发布，文档在它自己的
   [README](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-tapestore-oceanbase) 中。

## 为什么是 harness 而不是 framework

agentseek 不打算取代你的 agent framework。如果你已经在用 LangChain、
DeepAgents 或者自己的 orchestrator，把模型轮次走 `agentseek-langchain`，让 harness
管状态、通道和 tape 就好。如果你是新项目，捆绑的 Bub kernel 本身就够用。

正是 harness 这种形态让 [扩展模型](../explanation/extension-model.zh.md) 能保持
精简：五个可扩展点（项目指令、skills、plugins、MCP servers、contrib 包）按代价排
序，通常最便宜的答案就是对的答案。

## Bub、tape，以及 agentseek 站在哪里

agentseek **打包了 [Bub](https://github.com/bubbuild/bub)** —— 同一套 hook 优先的
turn pipeline、channel、tape、skills 和插件模型。`agentseek` 是发行版入口；
`.agentseek/` 和 `AGENTSEEK_*` 是面向项目的默认值。除了 CLI 命令替换之外，Bub 没有被
fork 也没有被改。完整关系见
[agentseek 和 Bub 的关系](../explanation/bub-relationship.zh.md)。

[Why we rewrote Bub](https://bub.build/posts/why-rewrite-bub/) 这篇文章解释了维护
模型：**小而严格的 kernel** 加 **松耦合的 plugin**。agentseek 在那张图里就是
**harness 和默认捆绑层** —— 它不试图把所有 store 和 channel 都自己实现。

## 从哪里开始

- **动手体验：** [教程](../tutorials/index.zh.md)。CLI 走查五分钟；first harness
  app 是大多数应用开发者真正想走的路径。
- **查事实：** [参考](../reference/index.zh.md)，包括环境变量、CLI、包、文件布局、
  Docker。
- **决定改动放在哪里：** [扩展模型](../explanation/extension-model.zh.md)。
- **仓库地址：** [ob-labs/agentseek on GitHub](https://github.com/ob-labs/agentseek)。
- **目录：** 站点上的 [Hub](../hub.zh.md) 收录了插件和技能；更广的 Bub 生态请看
  [hub.bub.build](https://hub.bub.build)。
