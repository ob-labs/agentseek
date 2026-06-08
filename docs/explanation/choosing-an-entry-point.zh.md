---
title: CLI 命令面
type: explanation
audience: [A1, A2, A4, A5]
runs: no
verified_on: 2026-06-08
sources:
  - README.md
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli.py
  - src/agentseek/lifecycle/app.py
  - entrypoint.sh
---

# CLI 命令面

AgentSeek 现在只有一个公开 CLI 入口：`agentseek`。

一个命令名之下，按工作流拆成三个稳定区域：

| 工作 | 命令 | 使用场景 |
| --- | --- | --- |
| 项目生命周期 | `new`, `dev`, `build`, `deploy` | 创建、运行、打包或部署项目。 |
| 运行时 | `chat`, `turn`, `gateway` | 与 harness 交互。 |
| 扩展与服务 | `plugin`, `ctx`, `skills`, `api`, `mcp` | 连接插件、上下文、skills、API 或 MCP server。 |

这个形态符合 AgentSeek 的实际使用方式：项目生命周期管理足够重要，应该是一等命令；
但它不应该要求独立包或独立命令名。运行时能力同样保留在同一个入口上，因为
`agentseek` 本身也是可执行 harness。

## 为什么拆命令组

- `new / dev / build / deploy` 是项目操作，可以发生在长运行 harness 启动之前。
- `chat / turn / gateway` 是运行时操作，会执行 harness。
- `plugin / ctx / skills / api / mcp` 负责把运行时连接到可选服务和工具。

这样可以避免根命令歧义：Bub 的根级 `run` 在 AgentSeek 中是 `agentseek turn`；
插件变更命令收敛到 `agentseek plugin` 下面。

## 生成项目

生成项目依赖 `agentseek`，因此 `uv sync` 后得到同一套命令面：

```bash
uv run agentseek new langchain/default
cd my-agent
uv sync
uv run agentseek dev
```

## Docker Compose

Compose 是面向运维的运行时封装。`entrypoint.sh` 准备 runtime home，把
`AGENTSEEK_*` 变量映射给 Bub，并在 workspace 未提供自定义 startup script 时启动
`agentseek gateway`。

## 影响

- 安装和文档都围绕 `agentseek`，不再围绕 companion lifecycle package。
- 旧的根命令形式故意无效，不依赖别名。
- Contrib 包仍然是可选运行时扩展，不是替代入口。

## 相关

- [CLI 参考](../reference/cli.zh.md)
- [包参考](../reference/packages.zh.md)
- [AgentSeek 与 Bub 的关系](bub-relationship.zh.md)
- [各样东西的位置](where-things-live.zh.md)
