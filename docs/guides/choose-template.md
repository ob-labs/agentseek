---
title: Choose a Template
type: how-to
audience: [A1, A2]
runs: no
verified_on: 2026-07-11
sources:
  - templates/index.json
  - docs/reference/templates.md
  - templates/bub/default/README.md
  - templates/deepagents/default/README.md
  - templates/deepagents/research/README.md
  - templates/deepagents/content-builder/README.md
  - templates/deepagents/sandbox/README.md
  - templates/langchain/default/README.md
  - templates/langchain/markdown-messages/README.md
  - templates/langchain/agentic-rag/README.md
  - templates/langchain/cli-remote/README.md
---

# Choose a Template

Use this guide before you create a project.

## Choose The Runtime Family

| Start with | When you need |
| --- | --- |
| `bub` | A lightweight Bub app, AG-UI gateway, and AgentSeek lifecycle commands. |
| `deepagents` | Planning, tool use, sub-agent workflows, sandbox-backed coding agents, or DeepAgents examples with local development. |
| `langchain` | LangChain or LangGraph app patterns, including RAG, markdown chat, or AG-UI integration. |

Every maintained template exposes AgentSeek lifecycle commands through
`.agentseek/lifecycle.toml`. The runtime choice still matters because the
generated app code is Bub, DeepAgents, LangChain, or LangGraph shaped.

## Pick By Project Goal

| Goal | Choose | Why |
| --- | --- | --- |
| Build the smallest Bub AG-UI app | `bub/default` | It starts a Bub gateway and Vite frontend with the least extra runtime surface. |
| Wrap a minimal DeepAgents runnable for AgentSeek | `deepagents/default` | It binds `create_deep_agent(...)` through `agentseek-langchain`. |
| Run a DeepAgents research workflow | `deepagents/research` | It includes search, tool streaming, sub-agent progress, and a React frontend. |
| Run a DeepAgents content workflow | `deepagents/content-builder` | It includes brand memory, skills, subagents, image generation, and streamed UI. |
| Build a sandbox-backed coding agent | `deepagents/sandbox` | It uses `create_deep_agent(...)` with Daytona by default and keeps the charged LangSmith Sandbox as an alternative. |
| Build a LangChain AG-UI app | `langchain/default` | It keeps the LangChain `create_agent(...)` shape and binds it through AgentSeek. |
| Start with a pure LangGraph-style chat UI | `langchain/markdown-messages` | It uses `langgraph dev`, `@langchain/react`, and markdown message rendering. |
| Build RAG over OceanBase seekdb | `langchain/agentic-rag` | It includes an agentic retrieval tool, ingest command, frontend, and OceanBase seekdb setup. |
| Connect to a remote LangGraph service | `langchain/cli-remote` | It bridges a remote LangGraph agent through `LangGraphClientRunnable`. |

## Choose AgentSeek-Wrapped Or Framework-Native

Use `bub/default`, `deepagents/default`, or `langchain/default` when you want
the generated app to run through the
AgentSeek/Bub gateway path.

Use `deepagents/research`, `deepagents/content-builder`, `deepagents/sandbox`,
`langchain/markdown-messages`, or `langchain/agentic-rag`
when you want a framework-native backend such as `langgraph dev`, still managed
by AgentSeek lifecycle commands.

Use `langchain/cli-remote` when the generated project should talk to an
already running LangGraph service instead of owning the graph process.

## Check Full Details

After you choose a starting point, use the template reference for exact paths
and supported create forms.

- [Create a Project](create-project.md)
- [Templates reference](../reference/templates.md)
- [Lifecycle Spec reference](../reference/lifecycle-spec.md)
