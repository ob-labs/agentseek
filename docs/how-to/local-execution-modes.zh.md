---
title: 本地执行模式
type: how-to
audience: [A2, A3, A4]
runs: yes
verified_on: 2026-06-25
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/run.py
  - src/agentseek/cli/commands/api.py
  - docs/how-to/run-locally.zh.md
  - docs/how-to/run-gateway.zh.md
  - docs/how-to/run-with-docker-compose.zh.md
---

# 本地执行模式

当你需要选择正确的本地入口时使用本页。这里说明 runtime 命令、project runner、gateway、API service 和 Docker Compose 路径之间的边界，但不重复完整的 [CLI 参考](../reference/cli.zh.md)。

## 选择入口

| 目标 | 命令 | 运行位置 |
| --- | --- | --- |
| 启动交互式终端对话 | `agentseek chat` | 已配置的 AgentSeek 环境 |
| 发送一条消息并退出 | `agentseek turn "message"` | 已配置的 AgentSeek 环境 |
| 监听 channel 消息 | `agentseek gateway` | 已安装 channel plugin 和凭据的 runtime 环境 |
| 本地运行生成的项目 | `agentseek run` | 生成的项目根目录 |
| 通过 Compose 运行生成的项目 | `agentseek run --mode compose` | 包含 Compose 文件的生成项目根目录 |
| 开发可选 API runtime | `agentseek api dev` | 已安装 `agentseek-api` 的环境 |

## Runtime 命令：`chat`、`turn` 和 `gateway`

当你想直接运行 AgentSeek runtime 时使用这些命令。

- `agentseek chat` 打开交互式 CLI chat session。这是测试模型配置和本地 runtime 连接最快的方式。
- `agentseek turn "message"` 将一条 inbound message 送入 framework pipeline，然后退出。适合脚本、smoke test 和可重复的命令行检查。
- `agentseek gateway` 启动消息监听器，例如 Telegram 或其他已安装的 channel plugin。当 AgentSeek 需要等待外部消息而不是终端输入时使用它。

`chat` 和 `turn` 见[本地运行](run-locally.zh.md)，channel 设置见[运行 gateway](run-gateway.zh.md)。

## Project runner：`agentseek run`

在生成的项目根目录中使用 `agentseek run`，用于启动项目循环并打开 frontend。

在 `auto` 模式下，AgentSeek 会检测项目结构：

1. 如果根目录包含 `docker-compose.yml`、`docker-compose.yaml`、`compose.yml` 或 `compose.yaml`，使用 Compose mode。
2. 否则，如果根目录包含 `pyproject.toml`，并且有 `app.py`、`main.py` 或 `serve` / `dev` script，使用 Python mode。

如果你已经知道要使用哪条路径，可以显式指定：

```bash
uv run agentseek run --mode compose
uv run agentseek run --mode python
```

`agentseek run` 还会从 `.env` 读取 `PORT` 或 `FRONTEND_PORT`，探测 frontend 的 host 和 port，并在未传入 `--no-browser` 时打开浏览器。

## API runtime：`agentseek api dev`

`agentseek api` 是可选 `agentseek-api` package 的转发命令组。开发或启动 API runtime 本身时使用 `agentseek api dev`。

它和 project-level `agentseek run` 的边界不同：

| 命令 | 边界 |
| --- | --- |
| `agentseek run` | 从生成的项目目录启动该项目。 |
| `agentseek api dev` | 启动 `agentseek-api` 暴露的可选 API service。 |

如果当前环境没有安装 `agentseek-api`，该命令会报告依赖需求，而不是启动项目。

## Docker Compose 路径

Compose 有两条路径：

- `docker compose up` 直接启动 Compose stack。需要 Docker 的常规 workflow 时使用它。
- `agentseek run --mode compose` 让 AgentSeek 启动 Compose，等待 frontend ready，并可选择打开浏览器。

容器设置和环境变量见 [Docker Compose](run-with-docker-compose.zh.md)。如果需要生成部署 artifact，而不是本地开发循环，请看[构建与部署](build-and-deploy.zh.md)。

## 相关页面

- [本地运行](run-locally.zh.md)
- [运行 gateway](run-gateway.zh.md)
- [Docker Compose](run-with-docker-compose.zh.md)
- [CLI 参考](../reference/cli.zh.md)
