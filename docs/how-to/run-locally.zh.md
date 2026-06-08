---
title: 如何在本地运行 agentseek
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli.py
  - contrib/agentseek-cli/README.md
  - contrib/agentseek-cli/pyproject.toml
  - docs/index.md
---

# 如何在本地运行 agentseek

当你想在 **harness 环境** 中做一个快速本地回路时使用本指南
（总览里的路径 B：本仓库 `uv sync` 之后，或生成项目各自 `uv sync`
之后）。具体能用哪个命令，取决于它归哪个包所有。

| 目标 | 命令 | 说明 |
| --- | --- | --- |
| 健全性验证一次 chat turn | `agentseek chat` | harness 运行时 CLI。路径 B 可用。 |
| 运行生成的项目 (模板结构) | `agentseek dev` | 启动 frontend + gateway。归 `agentseek-cli` 所有；在合并后的同一 `agentseek` 命令面中可用。 |

## 前置条件

- 已配置模型与密钥 —— 见 [如何配置模型提供商](configure-model.zh.md)。
- 一个可用的 harness 环境（在本仓库 `uv sync`，或在生成项目里
  `uv sync`）。
- `agentseek dev` 需要：通过 `agentseek new` 创建的项目 (见
  [模板参考](../reference/templates.zh.md)) **或** 当前目录下已有的兼容
  `agentseek-cli` 的布局。

## 选项 1 — `agentseek chat`

`agentseek chat` 归 **harness** 包所有。它是内置 CLI channel，并启用了生命周期 channel
(`src/agentseek/cli.py:83`)。用它在没有任何 frontend 的情况下对模型 /
MCP / skill 组合做健全性检查。

1. 确认 `.env` 中有模型与密钥。见 [如何配置模型提供商](configure-model.zh.md)。

2. 运行一个 session：

   ```bash title="not executed in this run"
   uv run agentseek chat
   ```

3. 可选标志 (来自 `agentseek chat --help`)：

   | 标志 | 默认值 | 描述 |
   | --- | --- | --- |
   | `--chat-id` | `local` | chat id。 |
   | `--session-id` | `None` | 可选 session id。 |

## 选项 2 — `agentseek dev`

`agentseek dev` 归 **`agentseek-cli`** 所有。在合并环境里，它会启动本地项目，
通常是 frontend (Vite) 加一个 gateway，并等待 frontend 就绪。

1. 在项目目录内：

   ```bash title="not executed in this run"
   uv run agentseek dev
   ```

2. 通过下列标志调整启动 (来自 `agentseek dev --help`)：

   | 标志 | 默认值 | 描述 |
   | --- | --- | --- |
   | `--port` | `.env` 中的 `$PORT`，否则 `3000` | frontend 端口。 |
   | `--host` | `127.0.0.1` | 探测就绪的主机。 |
   | `--no-browser` | off | 跳过打开默认浏览器。 |
   | `--wait-timeout` | `30` | 等待 frontend 的秒数。 |
   | `--mode` | `auto` | `auto`、`compose`、`python` 之一。 |

`--mode compose` 将工作交给 Docker Compose；见
[如何使用 Docker Compose 运行](run-with-docker-compose.zh.md)。`--mode python` 直接运行项目的 Python
入口。

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| 找不到 `agentseek chat` | 你现在是只装了 `agentseek-cli` 的路径 A 环境 | 改用 harness 环境（仓库或生成项目里执行 `uv sync`）。 |
| `agentseek chat` 在模型错误后悄然退出 | provider 拒绝了请求 | 用模型的 debug env 重跑，或用 `agentseek onboard` 重写配置。 |
| `agentseek dev` 等 frontend 超时 | 端口不匹配 | 传入 `--port <n>`，与 frontend 监听端口一致。 |
| `agentseek dev` 报 "not in a project" 退出 | 在非生成项目目录下选了 `--mode python` | 先运行 `agentseek new`，或改用 `--mode compose`。 |

## 回退

`Ctrl-C` 停止任一命令。两者都不会在 `.agentseek/` 运行时家目录
之外写持久化状态。

## 相关

- 操作指南: [如何运行 gateway](run-gateway.zh.md), [如何使用 Docker Compose 运行](run-with-docker-compose.zh.md),
  [如何配置模型提供商](configure-model.zh.md)
- 参考: [CLI 参考](../reference/cli.zh.md)
