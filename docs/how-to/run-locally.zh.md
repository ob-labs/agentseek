---
title: 如何本地运行 agentseek
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/run.py
---

# 如何本地运行 agentseek

当你要在本机运行 AgentSeek 时使用本页。

## 前置条件

- 已配置模型凭证。见[配置模型](configure-model.zh.md)。
- AgentSeek 可通过 `agentseek` 调用，或已安装在生成项目中。

## 启动 chat

```bash
agentseek chat
```

只有需要固定会话标识时，才传入 `--chat-id` 或 `--session-id`。

## 运行生成项目

在生成项目根目录中运行：

```bash
uv run agentseek run
```

该命令会启动项目循环并等待前端 ready。使用 `Ctrl-C` 停止。

如果前端使用非默认端口，显式传入端口：

```bash
uv run agentseek run --port 5173
```

## 排障

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| chat 无法调用模型 | provider 配置缺失或错误。 | 检查 `.env`。 |
| `agentseek run` 等待超时 | 前端监听了其他端口。 | 传入 `--port <n>`。 |
| `agentseek run` 立即退出 | 当前目录不是生成项目。 | 在生成项目根目录运行。 |

## 相关

- [CLI 参考](../reference/cli.zh.md)
- [运行 gateway](run-gateway.zh.md)
- [使用 Docker Compose 运行](run-with-docker-compose.zh.md)
