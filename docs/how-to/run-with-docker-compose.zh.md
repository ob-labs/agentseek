---
title: 如何使用 Docker Compose 运行
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-12
sources:
  - Dockerfile
  - docker-compose.yml
  - entrypoint.sh
---

# 如何使用 Docker Compose 运行

当你要在容器中运行 gateway 时使用本页。

## 前置条件

- Docker，且支持 `compose` 子命令。
- 一个包含 `docker-compose.yml` 的项目目录。
- `docker-compose.yml` 旁边有 `.env`，至少包含 `AGENTSEEK_MODEL` 和
  `AGENTSEEK_API_KEY`。

## 步骤

1. 启动容器。

   ```bash
   docker compose up --build
   ```

   这会启动容器栈，并在需要时重新构建镜像。使用 `docker compose down` 停止。

2. 必要时把运行时文件放到项目目录之外。

   ```bash title=".env"
   AGENTSEEK_DOCKER_WORKSPACE=/srv/agentseek-data
   ```

   Compose 会把该主机目录挂载到 `/workspace`。

3. 必要时指向项目内的 skills 或 MCP 配置。

   ```bash title=".env"
   AGENTSEEK_SKILLS_HOME=/workspace/.agents/skills
   AGENTSEEK_MCP_CONFIG_PATH=/workspace/.agents/mcp.json
   ```

4. 必要时替换默认命令。

   在挂载的 workspace 放入 `startup.sh`。entrypoint 会执行它，而不是默认的
   `agentseek gateway`。

## 回退

运行 `docker compose down` 停止容器。删除 `.env` 中的自定义值即可恢复默认值。

## 故障排查

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| 构建时报 frozen lock 错误。 | `uv.lock` 与项目不同步。 | 运行 `uv sync` 或 `uv lock` 后重建。 |
| 数据没有落到预期位置。 | workspace mount 指向项目目录。 | 设置 `AGENTSEEK_DOCKER_WORKSPACE`。 |
| 容器内没有加载 skills。 | `AGENTSEEK_SKILLS_HOME` 指向其他位置。 | 使用 `/workspace/.agents/skills`。 |
| 未读到 MCP。 | `.agents/mcp.json` 缺失，或路径不同。 | 创建文件或设置 `AGENTSEEK_MCP_CONFIG_PATH`。 |
| 容器启动了自定义命令。 | 存在 `startup.sh`。 | 删除或修改 `startup.sh`。 |

## 相关

- [环境变量](../reference/environment.zh.md)
- [构建与部署](build-and-deploy.zh.md)
- [配置 MCP 服务器](configure-mcp.zh.md)
