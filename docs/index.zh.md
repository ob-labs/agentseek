---
hide_sidebar: true
---

# AgentSeek 文档

AgentSeek 是数据库原生的 Agent Harness，用来构建运行时数据可持久化、可查询、可运维的
agent 应用。

这套文档主要回答三个问题：

1. 我应该从哪里开始？
2. 当前任务应该读哪篇指南？
3. 首次跑通后，细节参考在哪里？

## 快速入口

| 目标 | 从这里开始 |
| --- | --- |
| 创建模板项目 | [构建你的第一个 harness 应用](tutorials/02-first-harness-app.zh.md) |
| 运行 AgentSeek 本身 | [通过 CLI 快速演示](tutorials/01-quick-demo-cli.zh.md) |
| 配置模型凭证 | [配置模型提供方](how-to/configure-model.zh.md) |
| 本地运行生成项目 | [本地运行](how-to/run-locally.zh.md) |
| 构建和部署生成项目 | [构建和部署](how-to/build-and-deploy.zh.md) |

## 先选一个流程

| 流程 | 从这里开始 | 适合场景 |
| --- | --- |
| 从模板创建项目 | [构建你的第一个 harness 应用](tutorials/02-first-harness-app.zh.md) | 你需要一个可运行的应用脚手架。 |
| 运行 AgentSeek 本身 | [通过 CLI 快速演示](tutorials/01-quick-demo-cli.zh.md) | 你要评估或运维 harness runtime。 |

首次跑通之后，再按下一步任务选择：

| 需要 | 从这里开始 |
| --- | --- |
| 最小 [LangChain](https://github.com/langchain-ai/langchain) 应用 | [模板参考](reference/templates.zh.md)里的 `langchain/markdown-messages`。 |
| 完整产品形态的生成项目 | `langchain/default`，然后读[本地运行](how-to/run-locally.zh.md)和[构建和部署](how-to/build-and-deploy.zh.md)。 |
| [DeepAgents](https://docs.langchain.com/oss/deepagents) 项目 | 在[模板参考](reference/templates.zh.md)里比较 `deepagents/research`、`deepagents/content-builder` 和 `langchain/sandbox`。 |
| 不带 LangChain 的轻量应用 | 从 `bub/default` 模板开始。 |
| 要加入持久记忆 | 使用 [agentseek-contextseek](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-contextseek) 或 [ContextSeek](https://github.com/ob-labs/contextseek)。 |
| 要选择数据库后端 | 阅读 [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) 和[运行时数据模型](explanation/runtime-data-model.zh.md)。 |

## 参考细节

| 需要 | 参考 |
| --- | --- |
| 理解命令的组织方式 | [命令概览](explanation/cli-surface.zh.md) |
| 查看所有命令和参数 | [CLI 参考](reference/cli.zh.md) |
| 查看所有模板 | [模板参考](reference/templates.zh.md) |
| 理清包和仓库边界 | [包参考](reference/packages.zh.md) |

## 常用命令

```bash
# Browse templates
uvx agentseek create --list-templates

# Create a minimal LangChain project
uvx agentseek create langchain/markdown-messages

# Run AgentSeek itself
uv tool install agentseek
agentseek chat
```

## 文档地图

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="tutorials/">教程</a></h3>
    <p>第一个应用和常见项目设置的引导式演练。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/">操作指南</a></h3>
    <p>模型、本地运行、部署、gateway 和 ContextSeek 的任务式食谱。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="explanation/">概念解释</a></h3>
    <p>包边界、Bub、LangChain、扩展模型和运行时数据的设计说明。</p>
  </div>
  <div class="terminal-card">
    <h3><a href="reference/">参考</a></h3>
    <p>CLI 参数、模板、包、环境变量和文件布局的精确表格。</p>
  </div>
</div>
