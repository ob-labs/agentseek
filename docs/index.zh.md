---
hide_sidebar: true
---

# AgentSeek 文档

AgentSeek 是数据库原生的 Agent Harness，用来构建运行时数据可持久化、可查询、可运维的
agent 应用。

这套文档主要回答三个问题：

1. 我应该从哪个项目形态开始？
2. 我需要的能力属于哪个包或相邻项目？
3. 如何从本地开发走到 memory、storage、gateway 和 serving？

## 快速入口

| 目标 | 从这里开始 |
| --- | --- |
| 创建第一个生成项目 | [构建你的第一个 harness 应用](tutorials/02-first-harness-app.zh.md) |
| 选择模板 | [模板参考](reference/templates.zh.md) |
| 理清 CLI 入口 | [选择一个入口](explanation/choosing-an-entry-point.zh.md) |
| 配置模型凭证 | [配置模型提供方](how-to/configure-model.zh.md) |
| 本地运行生成项目 | [本地运行](how-to/run-locally.zh.md) |
| 构建和部署生成项目 | [构建和部署](how-to/build-and-deploy.zh.md) |

## 选择路径

| 你是... | 推荐路径 |
| --- | --- |
| 刚接触 [LangChain](https://github.com/langchain-ai/langchain) 或 agents | 从 `langchain/markdown-messages` 开始，然后读[构建你的第一个 harness 应用](tutorials/02-first-harness-app.zh.md)。 |
| 要构建完整产品界面 | 从 `langchain/default` 开始，然后读[本地运行](how-to/run-locally.zh.md)和[构建和部署](how-to/build-and-deploy.zh.md)。 |
| 要使用 [DeepAgents](https://docs.langchain.com/oss/deepagents) | 在[模板参考](reference/templates.zh.md)里比较 `deepagents/research`、`deepagents/content-builder` 和 `langchain/sandbox`。 |
| 直接使用 [Bub](https://github.com/bubbuild/bub) | 从 `bub/default` 开始，然后读 [AgentSeek 与 Bub 的关系](explanation/bub-relationship.zh.md)。 |
| 要加入持久记忆 | 使用 [agentseek-contextseek](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-contextseek) 或 [ContextSeek](https://github.com/ob-labs/contextseek)。 |
| 要选择数据库后端 | 阅读 [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) 和[运行时数据模型](explanation/runtime-data-model.zh.md)。 |

## 组件边界

AgentSeek 是一个套件，不是一个单体项目。配置、扩展和排查问题时，先确认能力属于哪个边界。

| 组件 | 边界 |
| --- | --- |
| `agentseek` | Runtime harness、gateway、skills/plugins、环境变量别名和本地 runtime state。 |
| `agentseek-cli` | 项目生命周期命令：`create`、`run`、`build`、`deploy`、`api`、`ctx`、`skills`。 |
| Templates | `templates/<framework>/<name>/` 下的 Cookiecutter 项目模板。 |
| `contrib/` | 桥接包，例如 `agentseek-langchain`、存储插件和 ContextSeek 集成。 |
| agentseek-api | 独立的生产 Agent Protocol server，用于服务 LangGraph 应用。 |
| ContextSeek | 独立的语义上下文和 memory 系统，提供 HTTP、MCP、Python SDK 和 LangChain middleware。 |
| langchain-oceanbase | 独立的 LangChain 存储集成，面向 OceanBase、seekdb 和 MySQL。 |

## 常用命令

```bash
# Browse templates
uvx --from agentseek-cli agentseek create --template

# Create a minimal LangChain project
uvx --from agentseek-cli agentseek create langchain/markdown-messages

# Run repository checks
make check
make test
make docs-test
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
