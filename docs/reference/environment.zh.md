---
title: 环境变量参考
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - entrypoint.sh
  - docker-compose.yml
---

# 环境变量参考

agentseek 从两个并行的命名空间读取其运行时配置：

- `AGENTSEEK_*` — 面向项目的名称。
- `BUB_*` — 运行时最终消费的上游 Bub 名称。

在启动时，`apply_agentseek_env_aliases()` 会将每个 `AGENTSEEK_<NAME>` 复制到对应的
`BUB_<NAME>` 槽位，**前提是 `BUB_<NAME>` 尚未设置**（`setdefault`）。
参见 `src/agentseek/env.py:56`。

## 由 `apply_agentseek_env_aliases` 设置的默认值

| 变量 | 默认值 | 定义于 |
| --- | --- | --- |
| `BUB_HOME` | `Path.cwd() / ".agentseek"` | `src/agentseek/env.py:70`、`:86` |
| `BUB_PROJECT` | `${BUB_HOME}/agentseek-project` | `src/agentseek/env.py:73` |

两个默认值都使用 `setdefault` 应用，因此显式值优先生效。

## 别名映射

| `AGENTSEEK_*` 名称 | 映射到 `BUB_*` | 说明 |
| --- | --- | --- |
| `AGENTSEEK_HOME` | `BUB_HOME` | 运行时 home 目录。 |
| `AGENTSEEK_PROJECT` | `BUB_PROJECT` | `agentseek plugin install` 使用的 plugin sandbox。 |
| `AGENTSEEK_WORKSPACE_PATH` | `BUB_WORKSPACE_PATH` | workspace 根目录，由 Docker entrypoint 使用（`entrypoint.sh:5`）。 |
| `AGENTSEEK_SKILLS_HOME` | `BUB_SKILLS_HOME` | skill 源目录（`entrypoint.sh:8`）。 |
| `AGENTSEEK_MCP_CONFIG_PATH` | `BUB_MCP_CONFIG_PATH` | MCP 配置文件路径。 |
| `AGENTSEEK_MODEL` | `BUB_MODEL` | 模型标识（例如 `openrouter:free`）。 |
| `AGENTSEEK_API_KEY` | `BUB_API_KEY` | 已配置 provider 的 API key。 |
| `AGENTSEEK_API_BASE` | `BUB_API_BASE` | 与 OpenAI 兼容的 base URL。 |
| `AGENTSEEK_MAX_STEPS` | `BUB_MAX_STEPS` | 模型 / tool 循环上限。 |
| `AGENTSEEK_MAX_TOKENS` | `BUB_MAX_TOKENS` | 响应 token 预算。 |
| `AGENTSEEK_MODEL_TIMEOUT_SECONDS` | `BUB_MODEL_TIMEOUT_SECONDS` | 模型请求超时。 |

该映射会从 pydantic-settings 可见的所有 `AGENTSEEK_<SUFFIX>` 变量动态构建
（`src/agentseek/env.py:91`、`:105`）。表中仅列出常用的后缀；任何新的
`AGENTSEEK_<SUFFIX>` 都会自动别名到 `BUB_<SUFFIX>`。

## 进程内消费的设置

| 设置 | 类型 | 默认值 | 来源 |
| --- | --- | --- | --- |
| `AGENTSEEK_CONSOLE` | bool | `False` | `src/agentseek/env.py:48` — 启用 Logfire console 输出。 |

## 仅 Docker 使用的变量

这些变量由 `entrypoint.sh` 与 `docker-compose.yml` 消费，在容器之外没有进程内效果。

| 变量 | compose 中的默认值 | 来源 |
| --- | --- | --- |
| `AGENTSEEK_DOCKER_WORKSPACE` | `.`（仓库根目录） | `docker-compose.yml:15` |
| `AGENTSEEK_WORKSPACE_PATH` | `/workspace` | `docker-compose.yml:8`、`entrypoint.sh:5` |
| `AGENTSEEK_HOME` | `/workspace/.agentseek` | `docker-compose.yml:9`、`entrypoint.sh:6` |
| `AGENTSEEK_PROJECT` | `/workspace/.agentseek/agentseek-project` | `docker-compose.yml:10`、`entrypoint.sh:9` |
| `AGENTSEEK_SKILLS_HOME` | `/workspace/.agents/skills` | `docker-compose.yml:11`、`entrypoint.sh:8` |
| `AGENTSEEK_MCP_CONFIG_PATH` | `/workspace/.agents/mcp.json` | `docker-compose.yml:12`、`entrypoint.sh:11` |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | `sqlite+pysqlite:////workspace/.agentseek/agentseek-tapes.db` | `docker-compose.yml:13` |

## `.env` 加载

`AgentseekSettings` 与别名探测都会以 `env_ignore_empty=True` 从当前工作目录加载 `.env`
（`src/agentseek/env.py:38`、`:26`）。`.env` 中的空值会被忽略。进程环境优先于 `.env`。

## 优先级

对于运行时看到的任一变量，靠前者优先：

1. 进程环境中针对 `BUB_*` 名称的显式值。
2. 进程环境中针对 `AGENTSEEK_*` 名称的显式值（别名到 `BUB_*`）。
3. `.env` 中针对 `BUB_*` 名称的值。
4. `.env` 中针对 `AGENTSEEK_*` 名称的值（别名到 `BUB_*`）。
5. 由 `_apply_agentseek_bub_location_defaults` 应用的默认值（仅适用于 `BUB_HOME` 与 `BUB_PROJECT`）。

对于同一项设置，`BUB_*` 总是优先于 `AGENTSEEK_*`，因为
`apply_agentseek_env_aliases` 使用了 `setdefault`（`src/agentseek/env.py:63`）。

## 另请参阅

- 操作指南：[如何配置模型提供商](../how-to/configure-model.zh.md)、[如何配置 MCP server](../how-to/configure-mcp.zh.md)、
  [如何配置 Docker 工作区](../how-to/configure-docker-workspace.zh.md)
- 概念解释：[agentseek 与 Bub 的关系](../explanation/bub-relationship.zh.md)
