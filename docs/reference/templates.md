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
| `deepagents/content-builder` | DeepAgents content builder with writing workflows, image generation, local UI, and AgentSeek lifecycle spec. |
| `deepagents/default` | Minimal DeepAgents app with AgentSeek lifecycle spec. |
| `deepagents/research` | DeepAgents research app with search workflow, local UI, and AgentSeek lifecycle spec. |
| `langchain/agentic-rag` | LangChain agentic RAG with OceanBase vector search and AgentSeek lifecycle spec. |
| `langchain/agentic-rag-openvino` | LangChain agentic RAG with local OpenVINO models and AgentSeek lifecycle spec. |
| `langchain/cli-remote` | LangChain template for connecting the local lifecycle workflow to a remote LangGraph service. |
| `langchain/default` | LangChain agent app with local web UI and AgentSeek lifecycle spec. |
| `langchain/markdown-messages` | LangChain chat app with markdown message rendering and AgentSeek lifecycle spec. |
| `langchain/sandbox` | Sandbox-backed coding agent with local UI and AgentSeek lifecycle spec. |

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
