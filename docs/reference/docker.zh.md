---
title: Docker 参考
type: reference
audience: [A4]
runs: no
verified_on: 2026-05-28
sources:
  - Dockerfile
  - entrypoint.sh
  - docker-compose.yml
---

# Docker 参考

本页镜像了验证日期的 `Dockerfile`、`entrypoint.sh` 与 `docker-compose.yml`。
任务说明请参见 [如何使用 Docker Compose 运行](../how-to/run-with-docker-compose.zh.md)。

## 镜像

| 属性 | 值 | 来源 |
| --- | --- | --- |
| Base image | `python:3.12-slim` | `Dockerfile:2` |
| `uv` 来源 | `ghcr.io/astral-sh/uv:latest`（复制到 `/bin/uv`） | `Dockerfile:3` |
| 额外 apt 包 | `tini`、`git` | `Dockerfile:6` |
| Workdir (build) | `/app` | `Dockerfile:11` |
| Workdir (run) | `/workspace` | `Dockerfile:25` |
| 构建环境 | `UV_LINK_MODE=copy`、`UV_COMPILE_BYTECODE=1`、`PYTHONUNBUFFERED=1` | `Dockerfile:17` |
| 安装命令 | `uv sync --frozen --no-dev` | `Dockerfile:21` |
| Entrypoint | `/usr/bin/tini --` | `Dockerfile:27` |
| 默认 CMD | `/app/entrypoint.sh` | `Dockerfile:28` |

整棵目录树在 `uv sync` 之前会被复制到 `/app`，因为 `contrib/` 下的 uv workspace
成员必须存在，lockfile 才能解析。

## Compose 服务

`docker-compose.yml` 定义了一个 `app` 服务：

| 属性 | 值 | 来源 |
| --- | --- | --- |
| 构建上下文 | `.` | `docker-compose.yml:3` |
| `env_file` | `.env` | `docker-compose.yml:6` |
| 卷挂载 | `${AGENTSEEK_DOCKER_WORKSPACE:-.}:/workspace` | `docker-compose.yml:15` |
| 重启策略 | `unless-stopped` | `docker-compose.yml:16` |

## Compose `environment` 块

| 变量 | 值 | 来源 |
| --- | --- | --- |
| `AGENTSEEK_WORKSPACE_PATH` | `/workspace` | `docker-compose.yml:8` |
| `AGENTSEEK_HOME` | `/workspace/.agentseek` | `docker-compose.yml:9` |
| `AGENTSEEK_PROJECT` | `/workspace/.agentseek/agentseek-project` | `docker-compose.yml:10` |
| `AGENTSEEK_SKILLS_HOME` | `/workspace/.agents/skills` | `docker-compose.yml:11` |
| `AGENTSEEK_MCP_CONFIG_PATH` | `/workspace/.agents/mcp.json` | `docker-compose.yml:12` |
| `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | `sqlite+pysqlite:////workspace/.agentseek/agentseek-tapes.db`（可覆盖） | `docker-compose.yml:13` |

## Entrypoint 解析顺序

`entrypoint.sh` 按以下顺序解析每个变量；首个非空值生效：

| 步骤 | 变量 | 检查顺序（首个非空值生效） | 来源 |
| --- | --- | --- | --- |
| 1 | `workspace_path` | `BUB_WORKSPACE_PATH` → `AGENTSEEK_WORKSPACE_PATH` → `/workspace` | `entrypoint.sh:5` |
| 2 | `agentseek_home` | `BUB_HOME` → `AGENTSEEK_HOME` → `${workspace_path}/.agentseek` | `entrypoint.sh:6` |
| 3 | `skills_target` | `${workspace_path}/.agents/skills`（固定） | `entrypoint.sh:7` |
| 4 | `skills_home` | `BUB_SKILLS_HOME` → `AGENTSEEK_SKILLS_HOME` → `${skills_target}` | `entrypoint.sh:8` |
| 5 | `project_home` | `BUB_PROJECT` → `AGENTSEEK_PROJECT` → `${agentseek_home}/agentseek-project` | `entrypoint.sh:9` |
| 6 | `mcp_config_target` | `${agentseek_home}/mcp.json`（固定） | `entrypoint.sh:10` |
| 7 | `mcp_config_source` | `BUB_MCP_CONFIG_PATH` → `AGENTSEEK_MCP_CONFIG_PATH` → `${workspace_path}/.agents/mcp.json`（若该文件存在） | `entrypoint.sh:11`、`:13` |

随后，所有解析得到的值都会同时以 `BUB_*` 和 `AGENTSEEK_*` 重新导出
（`entrypoint.sh:17`）。

## 文件系统操作

| 操作 | 条件 | 来源 |
| --- | --- | --- |
| `mkdir -p ${BUB_HOME} ${BUB_PROJECT} ${workspace_path}/.agents` | 始终 | `entrypoint.sh:28` |
| `mkdir -p ${skills_target}` | 当 `skills_home == skills_target` 时 | `entrypoint.sh:30` |
| `mkdir -p ${skills_home}; ln -sfn ${skills_home} ${skills_target}` | 当 `skills_home != skills_target` 时 | `entrypoint.sh:33` |
| `ln -sfn ${mcp_config_source} ${mcp_config_target}` | 当 source 已设置、存在且与 target 不同时 | `entrypoint.sh:37` |

## 启动顺序

1. 若 `${workspace_path}/startup.sh` 存在，则 `exec bash` 执行它（`entrypoint.sh:41`）。
2. 否则 `exec /app/.venv/bin/agentseek gateway`（`entrypoint.sh:45`）。

因此，用户提供的 `startup.sh` 会完全替换默认的 `agentseek gateway` 调用。

## 另请参阅

- 操作指南：[如何使用 Docker Compose 运行](../how-to/run-with-docker-compose.zh.md)、
  [如何配置 Docker 工作区](../how-to/configure-docker-workspace.zh.md)
- 参考：[环境变量参考](environment.zh.md)、[文件布局参考](file-layout.zh.md)
