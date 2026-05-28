---
title: 如何配置 Docker workspace
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-05-28
sources:
  - docker-compose.yml
  - entrypoint.sh
---

# 如何配置 Docker workspace

当你想让 Compose 挂载不同的宿主目录、想重新定位 plugin sandbox 或
skills 文件夹，或者想要不同的容器内 MCP 源路径时使用本指南。

## 前置条件

- 已安装 Docker 与 Docker Compose。
- 已 checkout 该仓库 (Compose 从 `.` 构建)。

## 步骤

1. 选定要覆盖的项。默认值如下：

   | 变量 | compose 中的默认值 | 来源 |
   | --- | --- | --- |
   | `AGENTSEEK_DOCKER_WORKSPACE` | `.` | `docker-compose.yml:15` |
   | `AGENTSEEK_WORKSPACE_PATH` | `/workspace` | `docker-compose.yml:8` |
   | `AGENTSEEK_HOME` | `/workspace/.agentseek` | `docker-compose.yml:9` |
   | `AGENTSEEK_PROJECT` | `/workspace/.agentseek/agentseek-project` | `docker-compose.yml:10` |
   | `AGENTSEEK_SKILLS_HOME` | `/workspace/.agents/skills` | `docker-compose.yml:11` |
   | `AGENTSEEK_MCP_CONFIG_PATH` | `/workspace/.agents/mcp.json` | `docker-compose.yml:12` |
   | `AGENTSEEK_TAPESTORE_SQLALCHEMY_URL` | `${AGENTSEEK_HOME}` 下的 sqlite | `docker-compose.yml:13` |

2. 把覆盖项放进 `docker-compose.yml` 旁边的 `.env`。Compose 会
   通过 `env_file: .env` 自动读取 (`docker-compose.yml:6`)。

   ```bash title=".env"
   # Mount a different host directory at /workspace
   AGENTSEEK_DOCKER_WORKSPACE=/srv/agentseek-data
   # Override the in-container MCP source
   AGENTSEEK_MCP_CONFIG_PATH=/workspace/custom/mcp.json
   ```

3. 启动容器，让 entrypoint 重新解析变量。解析顺序见
   `../reference/docker.md#entrypoint-resolution-order`。

   ```bash title="not executed in this run"
   docker compose up --build
   ```

   TODO(reviewer): run `docker compose up --build` and capture entrypoint
   logs to confirm the override path is taken.

### CLI 快捷方式

你也可以按次覆盖：

```bash title="not executed in this run"
AGENTSEEK_DOCKER_WORKSPACE=/srv/agentseek-data docker compose up
```

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| 容器误写到仓库根目录 | 未设置 `AGENTSEEK_DOCKER_WORKSPACE`，默认是 `.` | 在 `docker compose up` 前将其设为你的数据目录。 |
| 容器内未加载 skill | `AGENTSEEK_SKILLS_HOME` 指向 `/workspace/.agents/skills` 之外，而你期望 Bub 去别处扫描 | entrypoint 会把源 symlink 到 `/workspace/.agents/skills` (`entrypoint.sh:33`)；确认 Bub 在扫该 symlink。 |
| 未读到 MCP | `.agents/mcp.json` 缺失且 `AGENTSEEK_MCP_CONFIG_PATH` 未设置 | 要么创建文件，要么设置变量。 |

## 回退

`docker compose down` 停止容器。删除或注释 `.env` 中的覆盖项
即可恢复默认值。

## 相关

- 操作指南: `run-with-docker-compose.md`, `configure-mcp.md`
- 参考: `../reference/docker.md`, `../reference/environment.md`
