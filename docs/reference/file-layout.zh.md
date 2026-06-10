---
title: 文件布局参考
type: reference
audience: [A2, A4]
runs: no
verified_on: 2026-06-08
sources:
  - src/agentseek/env.py
  - entrypoint.sh
---

# 文件布局参考

除非通过环境变量覆盖，AgentSeek runtime 状态位于当前 workspace 内。

| 路径 | 创建者 | 用途 |
| --- | --- | --- |
| `.agentseek/` | `agentseek` runtime | AgentSeek 运行时 home 目录。 |
| `.agentseek/agentseek-project/` | `agentseek plugin install` | 用于解析插件依赖的 uv project。 |
| `.agentseek/mcp.json` | 用户或 Docker entrypoint | 默认 MCP 配置路径。 |
| `.agents/skills/` | 用户 | 项目本地 skills。 |
| `.agents/mcp.json` | 用户 | MCP 配置文件——Docker 会将其复制到 `.agentseek/mcp.json`。 |

## 环境变量覆盖

| 变量 | 覆盖内容 |
| --- | --- |
| `AGENTSEEK_HOME` / `BUB_HOME` | Runtime home。 |
| `AGENTSEEK_PROJECT` / `BUB_PROJECT` | Plugin sandbox path。 |
| `AGENTSEEK_MCP_CONFIG_PATH` / `BUB_MCP_CONFIG_PATH` | MCP config path。 |

两个前缀同时存在时，`BUB_*` 优先。见[环境变量参考](environment.zh.md)。
