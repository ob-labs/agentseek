---
title: 命令概览
type: explanation
audience: [A1, A2, A4, A5]
runs: no
verified_on: 2026-06-08
sources:
  - README.md
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/surface.py
  - entrypoint.sh
---

# 命令概览

AgentSeek 的所有功能通过 `agentseek` 命令访问，按使用场景分为三组：

| 目标 | 命令 | 使用场景 |
| --- | --- | --- |
| 项目管理 | `create`, `run`, `build`, `deploy` | 创建、运行、打包或部署项目。 |
| 运行时 | `chat`, `turn`, `gateway` | 与 harness 交互。 |
| 扩展与服务 | `plugin`, `ctx`, `skills`, `api`, `mcp` | 连接插件、上下文、skills、API 或 MCP server。 |

## 生成项目

生成项目以 `agentseek` 为依赖，`uv sync` 后即可使用相同的命令。典型流程：

```bash
uv run agentseek create langchain/default
cd my-agent
uv sync
uv run agentseek run
```

## Docker Compose

Compose 是面向运维的运行时封装。`entrypoint.sh` 准备 runtime home，并在
workspace 未提供自定义 startup script 时启动 `agentseek gateway`。

## 须知

- 安装 `agentseek` 即可，没有单独的 CLI 包。
- 旧的根命令形式不再支持，请使用上面列出的分组命令。
- Contrib 包是可选的运行时扩展，不是替代入口。

## 相关

- [CLI 参考](../reference/cli.zh.md)
- [包参考](../reference/packages.zh.md)
- [AgentSeek 与 Bub 的关系](bub-relationship.zh.md)
- [项目结构](where-things-live.zh.md)
