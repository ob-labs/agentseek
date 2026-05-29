---
title: 如何运行 gateway
type: how-to
audience: [A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - entrypoint.sh
  - docs/index.md
---

# 如何运行 gateway

当你需要一个 **长期运行** 的进程来监听各 channel (Feishu、
Telegram、AG-UI 等) 时使用本指南。`agentseek gateway` 归 **harness**
包所有，因此本页默认你已经在路径 B：本仓库 `uv sync` 之后、生成项目
`uv sync` 之后，或包装了同一套 harness 的 Docker Compose 环境中。

## 前置条件

- 你想启用的 channel plugin 已安装在运行时环境中
  (例如 `bub-feishu` 默认随 agentseek 发布 —— `pyproject.toml:20`)。
- `.env` 中有 channel 凭据。

## 步骤

1. 启用所需 channel。默认情况下，`agentseek gateway` 会启动所有
   注册过的 channel。

   ```bash
   uv run agentseek gateway --help
   ```

   ```text title="output"
   Usage: agentseek gateway [OPTIONS]

    Start message listeners(like telegram).

   ╭─ Options ─────────────────────────────────────────────╮
   │ --enable-channel  TEXT  Channels to enable for CLI    │
   │                         (default: all)                │
   │ --help                  Show this message and exit.   │
   ╰───────────────────────────────────────────────────────╯
   ```

2. 启动 gateway：

   ```bash title="not executed in this run"
   uv run agentseek gateway --enable-channel telegram
   ```

3. 要在 Docker 内运行，直接把 stack 起来即可 —— `entrypoint.sh:45`
   默认会 exec `agentseek gateway`：

   ```bash title="not executed in this run"
   docker compose up
   ```

   如要在同一 entrypoint 下运行 `agentseek gateway` 之外的命令，
   在 workspace 中放置一个 `startup.sh`；entrypoint 会改为
   `exec bash` 它 (`entrypoint.sh:41`)。

### 适用范围

这个命令属于 harness 运行时 CLI。仅安装 `agentseek-cli` 的路径 A 环境
并不提供它。gateway 也没有单独的嵌入式 API。

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| 找不到 `agentseek gateway` | 你现在是只装了 `agentseek-cli` 的路径 A 环境 | 改用 harness 环境，或用 Docker Compose 包装它。 |
| channel 一直收不到消息 | 运行时环境缺少该 plugin | `uv run agentseek install <plugin>` 加入 sandbox。 |
| gateway 立即退出 | channel 凭据缺失 | 在日志中找到 channel 名称；把凭据加到 `.env`。 |
| Docker 内多个 gateway 互相竞争 | `startup.sh` 和默认 entrypoint 都跑了 | 二选一；`startup.sh` 是替换不是链式叠加。 |

## 回退

`Ctrl-C` 停止。Docker 中：`docker compose down`。除了各 channel plugin
自己存储的内容 (如 cursor 文件)，没有持久化状态。

## 相关

- 操作指南: [How to run agentseek locally](run-locally.md), [How to run with Docker Compose](run-with-docker-compose.md),
  [How to configure the Docker workspace](configure-docker-workspace.md)
- 参考: [CLI reference](../reference/cli.md), [Docker reference](../reference/docker.md)
