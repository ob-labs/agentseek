---
title: agentseek 与 Bub 的关系
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/__main__.py
  - pyproject.toml
  - entrypoint.sh
---

# agentseek 与 Bub 的关系

> **简而言之：** `agentseek` 是 Bub 的一个 distribution，而不是 fork。它启动同一个 framework，
> 在 `.agentseek/` 下添加 project-local 默认值，为 CLI 加上品牌，并让 `AGENTSEEK_*` 环境变量
> 作为对应 `BUB_*` 变量的兜底。当你需要不加修改的上游行为时，`bub` CLI 就在那里。

## 背景

[Bub](https://github.com/bubbuild/bub) 是 runtime kernel：一条 hook-first 的 turn 流水线、
channel、tape、skill，以及 plugin 模型。kernel 有意保持小巧；所有有意思的东西都是 plugin。

`agentseek` 把该 kernel 打包成 "在真实 workspace 中运行的真实项目"。这意味着 opinionated 的默认
设置（数据放在哪里、变量长什么样、install sandbox 叫什么名字）以及品牌化的 CLI。这并不意味着
替换或隐藏 Bub：`agentseek` 把 Bub 作为普通依赖（`bub>=0.3.7`），启动后 runtime 就是普通的 Bub。

## 工作原理

### 启动顺序

当你运行 `agentseek …` 时，entry point：

1. 把 `AGENTSEEK_*` 环境变量映射到对应的 `BUB_*` 名称下，这样栈中其余部分只从一个前缀读取配置。
2. 启动 `BubFramework`，请求一个 CLI app，然后将 Bub 内置命令替换为 AgentSeek 自己的品牌实现。

Docker entrypoint 同理：它解析 `BUB_*`/`AGENTSEEK_*` 配对并导出两者，然后在
`${workspace_path}/startup.sh` 存在时 exec 它，否则回退到 `agentseek gateway`。

### 环境变量 alias 映射

- 对于名字以 `AGENTSEEK_` 开头且值非空的每个变量，agentseek 会将 `BUB_<suffix>` 设为相同的值，
  **仅当 `BUB_<suffix>` 尚未设置时**（setdefault 语义）。
- 因此预先存在的 `BUB_*` 变量会胜过 `AGENTSEEK_*` alias。

此外，当缺失时有两个位置默认值会被应用：

| 变量 | 未设置时的默认值 |
| --- | --- |
| `BUB_HOME` | `${cwd}/.agentseek` |
| `BUB_PROJECT` | `${BUB_HOME}/agentseek-project` |

完整的逐变量表位于 [环境变量参考](../reference/environment.zh.md)。

### CLI 命令布局

AgentSeek 的 CLI 从 Bub app 出发，但呈现不同的命令面：

- **`onboard`** — 同样的配置收集流程，品牌化为 AgentSeek banner。
- **`chat`** — 启用 Bub 支持通道（`*.lifecycle`），让 MCP 等 helper 能在 CLI chat 会话中启动。
- **`plugin install / uninstall / update`** — 收敛到 `agentseek plugin` 下。使用
  `.agentseek/agentseek-project` sandbox，并将 `agentseek-*` 包直接路由到 PyPI。
- **`turn`** — Bub 的单消息 `run` 命令，用一个非歧义名称暴露。
- **`create / run / build / deploy`** — AgentSeek 拥有的项目生命周期命令。
- **`api / ctx / skills`** — AgentSeek 拥有的服务转发命令。

运行时行为（turn pipeline、channel、hook、tape）仍然原样流经 Bub。

## 为什么是这样

- **默认值属于 distribution，不属于 kernel。** Bub 保持通用；agentseek 拥有 "项目 workspace
  长什么样" 的决策权。
- **Alias 是单向的，且 BUB 优先。** Plugin 作者面向上游前缀编写代码，在 agentseek 下也能干净
  运行，因为 alias 只填空。
- **没有 Bub 的私有 fork。** Bub 是普通依赖，按版本固定。升级 Bub 就升级 agentseek。

## 实际使用中的表现

- `uv run bub --help` 和 `uv run agentseek --help` 命令面不同。AgentSeek 增加项目命令组，
  并将 runtime 命令重组到面板中。
- `AGENTSEEK_*` 的值在进程持续期间会渗入 `BUB_*`，除非 `BUB_*` 已被设置。
- 默认值（`.agentseek` home、`agentseek-project` sandbox）会在首次运行任何 `agentseek` 命令时
  出现。偏好系统级布局的运维人员应显式设置 `BUB_HOME` 和 `BUB_PROJECT`。
- 如果某个问题在 `agentseek` 下能复现但在 `bub` 下不能，直接用 `bub` 跑同一条命令来二分定位。

## 何时直接使用 `bub`

在以下情况下使用上游 CLI：

- 你想精确复现 [Bub Hub](https://hub.bub.build) 中文档里的示例。
- 你正在开发 Bub plugin，想确保它不依赖 agentseek 默认值。
- 你不希望 workspace 中出现 `.agentseek/` 目录，更愿意自己管理 `BUB_HOME`。
- 你在诊断一个 bug 究竟出在 Bub 还是出在 agentseek 层。

当你想要 opinionated 默认值时使用 `agentseek`：workspace-local home、AgentSeek plugin
sandbox、chat 模式下的支持通道、项目命令组，以及 `AGENTSEEK_*` 命名。

## 相关

- 教程：[02 —— 构建你的第一个 harness 应用](../tutorials/02-first-harness-app.zh.md)
- 操作指南：[如何安装插件](../how-to/install-a-plugin.zh.md),
  [如何配置模型提供商](../how-to/configure-model.zh.md)
- 参考：[环境变量参考](../reference/environment.zh.md),
  [CLI 参考](../reference/cli.zh.md)
- 概念解释：[运行时数据模型](runtime-data-model.zh.md)
- 外部：[Bub repository](https://github.com/bubbuild/bub),
  [Bub Hub](https://hub.bub.build)
