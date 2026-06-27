---
title: 选择模板
type: how-to
audience: [A1, A2]
runs: no
verified_on: 2026-06-27
sources:
  - templates/index.json
  - docs/reference/templates.zh.md
  - templates/bub/default/README.md
  - templates/bub/contextseek/README.md
  - templates/deepagents/default/README.md
  - templates/deepagents/research/README.md
  - templates/deepagents/content-builder/README.md
  - templates/langchain/default/README.md
  - templates/langchain/markdown-messages/README.md
  - templates/langchain/agentic-rag/README.md
  - templates/langchain/cli-remote/README.md
  - templates/langchain/sandbox/README.md
---

# 选择模板

创建项目前，先用这个指南选择起点。

## 选择运行时族

| 从这里开始 | 适合场景 |
| --- | --- |
| `bub` | 轻量 Bub 应用、AG-UI gateway 和 AgentSeek 生命周期命令。 |
| `deepagents` | 需要规划、工具调用、sub-agent 工作流，或 DeepAgents 本地开发示例。 |
| `langchain` | 需要 LangChain 或 LangGraph 应用形态，包括 RAG、Markdown chat、sandbox 或 AG-UI 集成。 |

所有维护中的模板都会通过 `.agentseek/lifecycle.toml` 暴露 AgentSeek
生命周期命令。运行时选择仍然重要，因为生成的应用代码会保持 Bub、
DeepAgents、LangChain 或 LangGraph 的形态。

## 按项目目标选择

| 目标 | 选择 | 原因 |
| --- | --- | --- |
| 构建最小 Bub AG-UI 应用 | `bub/default` | 它启动 Bub gateway 和 Vite frontend，额外运行时表面积最小。 |
| 给 Bub 应用加入语义记忆 | `bub/contextseek` | 它在 `bub/default` 上加入 ContextSeek memory 和 ctx HTTP API。 |
| 将最小 DeepAgents runnable 接入 AgentSeek | `deepagents/default` | 它通过 `agentseek-langchain` 绑定 `create_deep_agent(...)`。 |
| 运行 DeepAgents research 工作流 | `deepagents/research` | 它包含搜索、工具流式事件、sub-agent 进度和 React frontend。 |
| 运行 DeepAgents 内容工作流 | `deepagents/content-builder` | 它包含品牌记忆、skills、subagents、图像生成和 streamed UI。 |
| 构建 LangChain AG-UI 应用 | `langchain/default` | 它保留 LangChain `create_agent(...)` 形态，并通过 AgentSeek 接入。 |
| 从纯 LangGraph 风格 chat UI 开始 | `langchain/markdown-messages` | 它使用 `langgraph dev`、`@langchain/react` 和 Markdown 消息渲染。 |
| 基于 OceanBase / SeekDB 构建 RAG | `langchain/agentic-rag` | 它包含 agentic retrieval tool、ingest command、frontend 和 SeekDB 设置。 |
| 连接远程 LangGraph 服务 | `langchain/cli-remote` | 它通过 `LangGraphClientRunnable` 桥接远程 LangGraph agent。 |
| 构建 sandbox coding agent | `langchain/sandbox` | 它把 DeepAgents、LangSmith sandbox backend 和本地 UI 组合起来。 |

## 选择 AgentSeek 包装形态或框架原生形态

如果你希望生成应用走 AgentSeek/Bub gateway 路径，选择
`bub/default`、`bub/contextseek`、`deepagents/default` 或
`langchain/default`。

如果你希望保留 `langgraph dev` 等框架原生 backend，同时仍由 AgentSeek
生命周期命令管理本地开发，选择 `deepagents/research`、
`deepagents/content-builder`、`langchain/markdown-messages`、
`langchain/agentic-rag` 或 `langchain/sandbox`。

如果生成项目应该连接一个已经运行的 LangGraph 服务，而不是自己管理图进程，
选择 `langchain/cli-remote`。

## 查看完整细节

选定起点后，用模板参考页查看准确路径和支持的 create 形式。

- [创建项目](create-project.md)
- [模板参考](../reference/templates.md)
- [生命周期规范参考](../reference/lifecycle-spec.md)
