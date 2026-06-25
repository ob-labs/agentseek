---
title: Templates
type: reference
audience: [A1, A2]
runs: no
verified_on: 2026-06-23
sources:
  - templates/index.json
  - src/agentseek/cli/commands/create.py
---

# Templates

## Available Templates

| Template | Description |
| --- | --- |
| `bub/contextseek` | Bub agent with ContextSeek semantic memory and AgentSeek lifecycle spec. |
| `bub/default` | Lightweight Bub agent with AgentSeek lifecycle spec. |
| `deepagents/content-builder` | DeepAgents content builder with skills, subagents, image generation, streamed UI, and AgentSeek lifecycle spec. |
| `deepagents/default` | Local `create_deep_agent` runnable with AgentSeek lifecycle spec. |
| `deepagents/research` | DeepAgents research agent with Tavily search, streamed tool/sub-agent UI, and AgentSeek lifecycle spec. |
| `langchain/agentic-rag` | LangChain agentic RAG with OceanBase vector search and AgentSeek lifecycle spec. |
| `langchain/agentic-rag-openvino` | LangChain agentic RAG with local OpenVINO models and AgentSeek lifecycle spec. |
| `langchain/cli-remote` | Remote LangGraph CLI agent bridged through `LangGraphClientRunnable` with AgentSeek lifecycle spec. |
| `langchain/default` | LangChain `create_agent` plus CopilotKit middleware with AgentSeek lifecycle spec. |
| `langchain/markdown-messages` | LangChain `create_agent` and react-markdown frontend with AgentSeek lifecycle spec. |
| `langchain/sandbox` | DeepAgents sandbox coding agent with streamed UI and AgentSeek lifecycle spec. |

## Template Specs

| Form | Example |
| --- | --- |
| Type | `bub` |
| Type and name | `bub/default` |
| Absolute local path | `/path/to/template` |
| Git URL | `https://github.com/example/templates.git` |

## Selection And Discovery

| Command | Result |
| --- | --- |
| `agentseek create` | Select the type and template interactively. |
| `agentseek create --list-templates` | List all known templates. |
| `agentseek create bub --list-templates` | List only `bub` templates. |
| `agentseek create bub` | Resolve to `bub/default`. |
| `agentseek create bub/default` | Use the specific template. |
| `agentseek create bub --template default` | Use `bub/default`. |
| `agentseek create --template` | Compatibility entry point that lists templates. Prefer `--list-templates` in new scripts. |
