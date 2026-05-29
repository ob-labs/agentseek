---
title: 如何使用 Docker Compose 运行
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-05-28
sources:
  - Dockerfile
  - docker-compose.yml
  - entrypoint.sh
  - docs/index.md
---

# 如何使用 Docker Compose 运行

当你不想本地装 Python，仍希望获得捆绑的 gateway、MCP 连线与
skills 布局时使用本指南。从职责上说，这就是**给运维打包过的路径 B**：
容器里最终运行的是 harness 运行时 CLI，而不是独立的路径 A 生命周期 CLI。

## 前置条件

- 已安装 Docker (含 `compose` 子命令)。
- 已 checkout 该仓库 (Compose 从 `.` 构建)。
- 在 `docker-compose.yml` 旁的 `.env` 中至少配置了
  `AGENTSEEK_MODEL` 与 `AGENTSEEK_API_KEY`。见 `configure-model.md`。

## 步骤

1. (可选) 把 workspace 挂载指向仓库根目录之外的宿主目录：

   ```bash title=".env"
   AGENTSEEK_DOCKER_WORKSPACE=/srv/agentseek-data
   ```

   Compose 会把它代入 `${AGENTSEEK_DOCKER_WORKSPACE:-.}:/workspace`
   (`docker-compose.yml:15`)。

2. 构建镜像并启动服务：

   ```bash title="not executed in this run"
   docker compose up --build
   ```

   entrypoint 会把 `BUB_*` 与 `AGENTSEEK_*` 导出为 compose
   `environment:` 块中的值，准备 `.agentseek/` 与 `.agents/skills`，
   并在存在 `${workspace}/startup.sh` 时运行之，否则默认运行
   `agentseek gateway` (`entrypoint.sh:41`, `:45`)。

3. 在另一个 shell 中查看日志：

   ```bash title="not executed in this run"
   docker compose logs -f
   ```

### 容器内的 workspace 约定

| 宿主 (默认) | 容器 | 来源 |
| --- | --- | --- |
| 仓库根 | `/workspace` | `docker-compose.yml:15`, `entrypoint.sh:5` |
| `.agentseek/` | `/workspace/.agentseek/` | `docker-compose.yml:9` |
| `.agents/skills/` | `/workspace/.agents/skills/` | `docker-compose.yml:11` |
| `.agents/mcp.json` (若存在) | 链接到 `/workspace/.agentseek/mcp.json` | `entrypoint.sh:13`, `:37` |

### 替换默认命令

在 `${workspace}/startup.sh` 放一个可执行脚本。entrypoint 会
`exec bash startup.sh` 而不是 `agentseek gateway` (`entrypoint.sh:41`)。
用它来在一次性容器里运行 `agentseek chat`，或运行项目自定义的
二进制。

### CLI 快捷方式

```bash title="not executed in this run"
docker compose up --build       # build + start
docker compose logs -f          # watch
docker compose down             # stop + remove
```

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| 构建期 `uv sync --frozen --no-dev` 失败 | `uv.lock` 与 `pyproject.toml` workspace 成员脱节 | 在宿主上重跑 `uv sync` 刷新 lock；再重新构建。 |
| workspace 数据未持久化 | `AGENTSEEK_DOCKER_WORKSPACE` 仍是默认 `.` | 挂载一个真实的数据目录。 |
| 你期待在容器里直接拿到 `create` / `build` / `deploy` | Compose 默认启动的是 harness 运行时路径 | 这些生命周期命令请在路径 A，或在本地的合并开发环境里执行，不走默认容器 entrypoint。 |

## 回退

```bash title="not executed in this run"
docker compose down
docker image rm agentseek-app   # if you no longer need the image
```

删除你添加的 `.env` 条目。

## 相关

- 操作指南: `configure-docker-workspace.md`, `build-and-deploy.md`
- 参考: `../reference/docker.md`, `../reference/environment.md`
