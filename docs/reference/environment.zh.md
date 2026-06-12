---
title: 环境变量参考
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-06-12
sources:
  - src/agentseek/env.py
  - entrypoint.sh
  - docker-compose.yml
---

# 环境变量参考

## 命名空间

| 命名空间 | 作用 |
| --- | --- |
| `AGENTSEEK_*` | 面向项目的别名。 |
| `BUB_*` | Bub runtime 消费的变量。 |

## 默认值

| 变量 | 默认值 |
| --- | --- |
| `BUB_HOME` | `${cwd}/.agentseek` |
| `BUB_PROJECT` | `${BUB_HOME}/agentseek-project` |

## 别名映射

| `AGENTSEEK_*` | `BUB_*` | 说明 |
| --- | --- | --- |
| `AGENTSEEK_HOME` | `BUB_HOME` | Runtime home 目录。 |
| `AGENTSEEK_PROJECT` | `BUB_PROJECT` | Plugin environment 路径。 |
| `AGENTSEEK_WORKSPACE_PATH` | `BUB_WORKSPACE_PATH` | Workspace 根目录。 |
| `AGENTSEEK_SKILLS_HOME` | `BUB_SKILLS_HOME` | Skills 目录。 |
| `AGENTSEEK_MCP_CONFIG_PATH` | `BUB_MCP_CONFIG_PATH` | MCP 配置路径。 |
| `AGENTSEEK_MODEL` | `BUB_MODEL` | 模型标识。 |
| `AGENTSEEK_API_KEY` | `BUB_API_KEY` | Provider API key。 |
| `AGENTSEEK_API_BASE` | `BUB_API_BASE` | OpenAI-compatible base URL。 |
| `AGENTSEEK_MAX_STEPS` | `BUB_MAX_STEPS` | Model/tool 循环上限。 |
| `AGENTSEEK_MAX_TOKENS` | `BUB_MAX_TOKENS` | 响应 token 预算。 |
| `AGENTSEEK_MODEL_TIMEOUT_SECONDS` | `BUB_MODEL_TIMEOUT_SECONDS` | 模型请求超时。 |

## AgentSeek-only 设置

| 变量 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `AGENTSEEK_CONSOLE` | boolean | `false` | 启用 Logfire console 输出。 |

## Docker 变量

| 变量 | Compose 默认值 | 说明 |
| --- | --- | --- |
| `AGENTSEEK_DOCKER_WORKSPACE` | `.` | 挂载到容器中的 host workspace。 |
| `AGENTSEEK_WORKSPACE_PATH` | `/workspace` | 容器内 workspace 路径。 |
| `AGENTSEEK_HOME` | `/workspace/.agentseek` | 容器内 runtime home。 |
| `AGENTSEEK_PROJECT` | `/workspace/.agentseek/agentseek-project` | 容器内 plugin environment。 |
| `AGENTSEEK_SKILLS_HOME` | `/workspace/.agents/skills` | 容器内 skills 目录。 |
| `AGENTSEEK_MCP_CONFIG_PATH` | `/workspace/.agents/mcp.json` | 容器内 MCP 配置路径。 |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | `sqlite+pysqlite:////workspace/.agentseek/agentseek-tapes.db` | 默认 SQLAlchemy tape-store URL。 |

## 优先级

| 顺位 | 来源 |
| --- | --- |
| 1 | 进程环境中的 `BUB_*` 值。 |
| 2 | 进程环境中的 `AGENTSEEK_*` 值，别名到 `BUB_*`。 |
| 3 | `.env` 中的 `AGENTSEEK_*` 值，别名到 `BUB_*`。 |
| 4 | AgentSeek 为 `BUB_HOME` 和 `BUB_PROJECT` 设置的默认值。 |

## `.env`

| 行为 | 值 |
| --- | --- |
| 文件路径 | 当前工作目录下的 `.env`。 |
| 空值 | 忽略。 |
| `.env` 中的 `BUB_*` 值 | 不由别名探测注入。 |
