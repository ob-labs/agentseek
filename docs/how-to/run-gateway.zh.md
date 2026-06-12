---
title: 如何运行 gateway
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - entrypoint.sh
---

# 如何运行 gateway

当你要让 AgentSeek 监听 channel 消息时使用本页。

## 前置条件

- runtime 环境中已安装对应 channel plugin。
- `.env` 中已有 channel 凭证。

## 本地运行

查看选项：

```bash
agentseek gateway --help
```

启动一个 channel：

```bash
agentseek gateway --enable-channel telegram
```

使用 `Ctrl-C` 停止 listener。不传 `--enable-channel` 时会启动所有已注册 channel。

## Docker 中运行

```bash
docker compose up
```

停止容器栈：

```bash
docker compose down
```

如果挂载的 workspace 中存在 `startup.sh`，容器会运行该脚本，而不是默认
gateway 命令。

## 排障

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| `agentseek gateway` 不可用 | 当前环境未安装 AgentSeek。 | 用 `uv tool install agentseek` 安装，或把它加入项目依赖。 |
| channel 收不到消息 | plugin 或凭证缺失。 | 安装 plugin 并检查 `.env`。 |
| Docker 启动了其他进程 | 存在 `startup.sh`。 | 删除或修改 `startup.sh`。 |

## 相关

- [本地运行](run-locally.zh.md)
- [使用 Docker Compose 运行](run-with-docker-compose.zh.md)
