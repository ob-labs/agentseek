---
title: Templates
type: reference
audience: [A1, A2]
runs: no
verified_on: 2026-07-11
sources:
  - templates/index.json
  - src/agentseek/cli/commands/create.py
  - templates/deepagents/sandbox/README.md
---

# Templates

## Available Templates

| Template | Description |
| --- | --- |
| `bub/default` | Lightweight Bub agent with AgentSeek lifecycle spec. |
| `deepagents/content-builder` | DeepAgents content builder with writing workflows, image generation, local UI, and AgentSeek lifecycle spec. |
| `deepagents/default` | Minimal DeepAgents app with AgentSeek lifecycle spec. |
| `deepagents/research` | DeepAgents research app with search workflow, local UI, and AgentSeek lifecycle spec. |
| `deepagents/sandbox` | DeepAgents sandbox coding agent with Daytona by default, a charged LangSmith Sandbox alternative, local UI, and AgentSeek lifecycle spec. |
| `langchain/agentic-rag` | LangChain agentic RAG with OceanBase vector search and AgentSeek lifecycle spec. |
| `langchain/agentic-rag-openvino` | LangChain local RAG with OpenVINO models and AgentSeek lifecycle spec. |
| `langchain/cli-remote` | LangChain template for connecting the local lifecycle workflow to a remote LangGraph service. |
| `langchain/default` | LangChain agent app with local web UI and AgentSeek lifecycle spec. |
| `langchain/markdown-messages` | LangChain chat app with markdown message rendering and AgentSeek lifecycle spec. |

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
| `agentseek create --list-templates --filter rag` | List only templates whose spec or description matches `rag`. |
| `agentseek create bub --list-templates` | List only `bub` templates. |
| `agentseek create bub` | Resolve to `bub/default`. |
| `agentseek create bub/default` | Use the specific template. |
| `agentseek create bub --template default` | Use `bub/default`. |
| `agentseek create bub/default --output-dir ./generated` | Write the generated project below the selected directory. |
| `agentseek create --template` | Compatibility entry point that lists templates. Prefer `--list-templates` in new scripts. |
