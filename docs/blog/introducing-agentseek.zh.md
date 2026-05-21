# 认识 agentseek

**2026-05-18**

## 从 bubseek 到 agentseek

我们最早以 **bubseek** 这个名字发布过一批探索性工作。最初的方向是围绕 **intrinsic observability** 和运行在 **seekdb** 上的 insight-style agent，这一点可以在 OceanBase 工程博客 [Intrinsic Observability: Build an Insight Agent on seekdb](https://en.oceanbase.com/blog/26947000576) 中看到。随着产品边界逐步收敛到一个 **database-native Agent Harness**，而不是承载某个垂直分发里所有领域细节，我们把项目 **重新命名为 agentseek**，并继续在这个仓库和当前文档站里推进。

那篇文章解释了 **为什么 agent 轨迹应该留在数据库里**，以及 seekdb 如何承载它们；agentseek 延续的是同一个判断：**runtime data 本身就有价值**。不同的是，我们把 **产品边界** 明确收缩到了 **harness 和发行版默认值** 这一层，更深的领域产品和数据栈继续留在上游或 **contrib**。

## 我们要解决的问题

长期以来，数据库主要承载 **业务结果**：订单、用户、内容、索引、分析表。Agent 运行过程中的数据却经常漂在数据库之外：session context 在一个地方，tool call 和 trace 在另一个地方，日志和 eval artefact 又在其他流水线里。常见形态包括 JSONL 风格的本地流、Markdown 笔记，以及偶尔出现的 SQLite sidecar。

这在一次性任务里没有问题，但会让 **事后调试、回放、比较、评估和训练** 的成本快速变高：第一个消费者用完之后，数据很难不经过再次复制就服务于其他系统。团队接着又会叠加 observability 和 dataset 工具（比如 LangSmith 或 Phoenix），从而引入新的部署和运维面。

当 agent 从个人 demo 走向 **长期运行的团队基础设施** 时，这个趋势会更明显：“memory” 不再只是静态画像，而更像是 **trace-shaped、multi-layer 的索引体系**；真正有持久价值的，往往不只是最终答案，而是 **上下文如何被组装、工作如何推进、工具如何被调用、状态如何演进、错误和反馈如何被记录**。谁能直接承载这层数据底座，谁就更可能成为基础设施的一部分。

## 为什么是数据库原生 harness

agentseek **并不打算替代所有 agent framework**。它要做的是一个 **database-native Agent Harness**，再加上一些有态度的默认值和扩展面，使 **context、memory、task state、tool calls、traces、feedback 以及 eval material** 从一开始就落到 **单一、可查询、可复用** 的持久层里，并在后续继续为消费链路服务，而不需要再额外做一次 re-ingestion。

[ob-labs/agentseek](https://github.com/ob-labs/agentseek) 的 README 讲得很直接：把这些 runtime artefact 保留在同一个持久 substrate 上，这样同一份数据既能服务调试、回放、trajectory comparison，也能继续喂给 evaluation、analysis 和 training。

从数据库视角看，这里会自然导出两个工程结论，而我们的实现会刻意贴合这两点：

1. **运行时数据天然保持可查询**。例如“这一类 tool call 在一段时间内如何分布”或“这次失败前后的状态是什么”，都不需要在已有存储已经支持 SQL（并可选支持向量）的前提下，再额外挂一层索引系统。
2. **上下文、观测和下游复用共享一套基础设施**。默认路径不再是“session 在 A、metrics 在 B、训练导出在 C”。Harness 的职责是把 **写路径和语义** 讲清楚；至于你最后落到本地 SQLite、OceanBase 还是 [seekdb](https://github.com/oceanbase/seekdb)，那是部署和 **contrib** 层面的选择。

## Bub、tape，以及 agentseek 所在的位置

agentseek **打包了 [Bub](https://github.com/bubbuild/bub)**：同一套 **hook-first** turn pipeline、channels、**tape**、skills 和 plugin model，只是把 `agentseek` 作为发行版入口，并把 `.agentseek` / `AGENTSEEK_*` 作为项目侧默认值。

[Tape Systems](https://tape.systems/) 把 tape 定义为一种统一事实模型：append-only entries、anchors 和 derived views，让长期运行、观测、评估和训练可以建立在 **同一条 append-only fact stream** 上，而不是每个出口各自维护一份影子日志。Bub 在内核里非常认真地对待 tape，并通过 `provide_tape_store` 这类 hook 暴露持久化能力；这和“runtime data 应该留在数据库里”其实是同一条轴线。

[Why we rewrote Bub](https://bub.build/posts/why-rewrite-bub/) 这篇文章解释了它的维护模型：一个 **small, strict kernel**，外加 **loosely owned plugins**。agentseek 在这个图景中的位置，就是 **harness 和默认打包层**，而不是一个把所有 store 和 channel 都塞进来的单体系统。

## 从哪里开始

- **动手体验：** [快速开始](../docs/getting-started.md)。
- **仓库地址：** [ob-labs/agentseek on GitHub](https://github.com/ob-labs/agentseek)。
- **能力目录：** 当前站点上的 [目录](../hub.md) 收录了插件和技能；更广的 Bub 生态请看 [hub.bub.build](https://hub.bub.build)。
