---
title: 文件布局参考
type: reference
audience: [A2, A4]
runs: no
verified_on: 2026-06-12
sources:
  - src/agentseek/env.py
  - entrypoint.sh
---

# 文件布局参考

## 运行时路径

| 路径 | 创建者 | 用途 |
| --- | --- | --- |
| `.agentseek/` | AgentSeek runtime | 默认 runtime home。 |
| `.agentseek/agentseek-project/` | `agentseek plugin install` | 用于 plugin dependency resolution 的 uv project。 |
| `.agentseek/mcp.json` | 开发者或 Docker entrypoint | 默认 MCP 配置路径。 |
| `.agents/skills/` | 开发者 | Project-local skills。 |
| `.agents/mcp.json` | 开发者 | Docker 会链接到 runtime path 的 workspace MCP 配置。 |

## 覆盖变量

| 变量 | 覆盖内容 |
| --- | --- |
| `AGENTSEEK_HOME`, `BUB_HOME` | Runtime home。 |
| `AGENTSEEK_PROJECT`, `BUB_PROJECT` | Plugin environment path。 |
| `AGENTSEEK_MCP_CONFIG_PATH`, `BUB_MCP_CONFIG_PATH` | MCP config path。 |
