---
title: 如何使用 Docker Compose 运行
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-08
sources:
  - Dockerfile
  - docker-compose.yml
  - entrypoint.sh
---

# 如何使用 Docker Compose 运行

当你希望在容器中运行 AgentSeek gateway、MCP wiring 和 skills layout 时使用本页。

## 前置条件

- Docker，且支持 `compose` 子命令。
- 已 checkout 本仓库。
- `docker-compose.yml` 旁边有 `.env`，至少包含 `AGENTSEEK_MODEL` 和 `AGENTSEEK_API_KEY`。

## 启动

```bash title="not executed in this run"
docker compose up --build
```

entrypoint 会准备 `.agentseek/`，在存在 `.agents/mcp.json` 时创建链接，并默认启动
`agentseek gateway`。

## 挂载其他 workspace

```bash title=".env"
AGENTSEEK_DOCKER_WORKSPACE=/srv/agentseek-data
```

Compose 会把该主机目录挂载到 `/workspace`。

## 替换默认命令

在挂载的 workspace 放入 `startup.sh`。entrypoint 会执行它，而不是默认的
`agentseek gateway`。

## 排障

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 构建时报 frozen lock 错误 | `uv.lock` 与项目不同步 | 在 host 上运行 `uv sync` 或 `uv lock` 后重建。 |
| workspace 数据没有落到预期位置 | 默认 workspace mount 指向 `.` | 设置 `AGENTSEEK_DOCKER_WORKSPACE`。 |
| 容器启动了自定义命令 | 存在 `startup.sh` | 删除或修改 `startup.sh`。 |

## 相关

- [Docker 参考](../reference/docker.zh.md)
- [环境变量](../reference/environment.zh.md)
- [构建与部署](build-and-deploy.zh.md)
