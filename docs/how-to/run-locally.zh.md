---
title: 如何本地运行 agentseek
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-06-08
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/dev.py
---

# 如何本地运行 agentseek

当你想在本仓库或生成项目里快速跑一轮本地循环时使用本页。

## 前置条件

- 已配置模型凭证。见[配置模型](configure-model.zh.md)。
- 当前环境已经同步：在本仓库或生成项目中运行过 `uv sync`。

## 与 harness chat

```bash title="not executed in this run"
uv run agentseek chat
```

常用选项：

| 选项 | 默认值 | 说明 |
| --- | --- | --- |
| `--chat-id` | `local` | Chat id。 |
| `--session-id` | `None` | 可选 session id。 |

## 运行生成项目

在 `agentseek new` 创建的项目目录中：

```bash title="not executed in this run"
uv run agentseek dev
```

常用选项：

| 选项 | 默认值 | 说明 |
| --- | --- | --- |
| `--port` | `$PORT` 或 `3000` | 前端端口。 |
| `--host` | `127.0.0.1` | readiness host。 |
| `--no-browser` | off | 不打开浏览器。 |
| `--wait-timeout` | `30` | 等待前端 ready 的秒数。 |
| `--mode` | `auto` | `auto`、`compose` 或 `python`。 |

## 排障

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| `agentseek chat` 无法调用模型 | provider 配置缺失或错误 | 检查 `.env`，或运行 `agentseek onboard`。 |
| `agentseek dev` 等待超时 | 前端监听端口不同 | 传入 `--port <n>`。 |
| `agentseek dev` 在非项目目录退出 | 没有生成项目布局 | 先运行 `agentseek new`，或改用 `agentseek chat`。 |

## 相关

- [CLI 参考](../reference/cli.zh.md)
- [运行 gateway](run-gateway.zh.md)
- [使用 Docker Compose 运行](run-with-docker-compose.zh.md)
