---
title: 如何运行 gateway
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-06-08
sources:
  - src/agentseek/cli/runtime.py
  - entrypoint.sh
---

# 如何运行 gateway

当你需要一个长运行进程监听 Feishu、Telegram、AG-UI 等 channel 时使用本页。

## 前置条件

- Runtime 环境中已安装需要的 channel plugin。
- `.env` 中已有 channel 凭证。

## 本地运行

查看选项：

```bash
uv run agentseek gateway --help
```

启动一个 channel：

```bash title="not executed in this run"
uv run agentseek gateway --enable-channel telegram
```

不传 `--enable-channel` 时会启动所有已注册 channel。

## Docker 中运行

```bash title="not executed in this run"
docker compose up
```

仓库 entrypoint 会准备 runtime home，并默认启动 `agentseek gateway`。如果挂载的
workspace 中存在 `startup.sh`，该脚本会替换默认 gateway 命令。

## 排障

| 现象 | 可能原因 | 处理 |
| --- | --- | --- |
| `agentseek gateway` 不可用 | 环境尚未同步 | 先运行 `uv sync`，再用 `uv run agentseek gateway`。 |
| channel 收不到消息 | plugin 或凭证缺失 | 安装 plugin 并检查 `.env`。 |
| Docker 启动了错误进程 | 存在 `startup.sh` | 删除或修改 `startup.sh`。 |

## 相关

- [本地运行](run-locally.zh.md)
- [使用 Docker Compose 运行](run-with-docker-compose.zh.md)
- [Docker 参考](../reference/docker.zh.md)
