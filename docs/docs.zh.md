---
title: 文档
type: explanation
audience: [A1, A2, A3, A4, A5]
runs: no
verified_on: 2026-05-30
sources:
  - README.md
  - mkdocs.yml
  - docs/tutorials/index.md
  - docs/how-to/index.md
  - docs/explanation/index.md
  - docs/reference/index.md
---

# 文档

从最符合你当前任务的象限开始。

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="tutorials/">教程</a></h3>
    <p>带你从干净起点走到端到端结果的引导页。适合第一次跑通一条完整路径。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/">操作指南</a></h3>
    <p>面向具体任务的短路径指引。适合已经熟悉系统、只想完成一个目标的时候使用。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="explanation/">概念解释</a></h3>
    <p>设计动机与心智模型。适合想理解 agentseek 为什么长成现在这样的时候阅读。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="reference/">参考</a></h3>
    <p>权威事实清单：环境变量、CLI 命令、文件布局、包、模板与 Docker。</p>
  </div>
</div>

## 建议起点

- 第一次接触项目：从 [通过 CLI 快速演示](tutorials/01-quick-demo-cli.zh.md) 开始。
- 准备构建应用：先读[命令概览](explanation/cli-surface.zh.md)，再读[构建你的第一个 harness 应用](tutorials/02-first-harness-app.zh.md)。
- 来自 LangChain / DeepAgents：先读 [agentseek 与 LangChain 的关系](explanation/langchain-relationship.zh.md)，然后在 [模板参考](reference/templates.zh.md) 里选一个适合你的模板。
- 需要运维一个 workspace：进入 [操作指南](how-to/index.zh.md)，优先看 Docker Compose 和 gateway 相关页面。
- 需要查准确信息：直接打开 [参考](reference/index.zh.md)。
