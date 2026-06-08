---
title: agentseek 与 Bub 的关系
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - src/agentseek/cli.py
  - src/agentseek/__main__.py
  - pyproject.toml
  - entrypoint.sh
---

# agentseek 与 Bub 的关系

> **简而言之：** `agentseek` 这个 **harness 包** 是 Bub 的一个 distribution，而不是 fork。
> 它启动同一个 framework，在 `.agentseek/` 下添加 project-local 默认值，为 CLI 加上品牌，
> 并让 `AGENTSEEK_*` 环境变量作为对应 `BUB_*` 变量的兜底。当你需要不加修改的上游行为时，
> `bub` CLI 和 Python API 就在那里。

## 背景

[Bub](https://github.com/bubbuild/bub) 是 runtime kernel：一条 hook-first 的 turn 流水线、
channel、tape、skill，以及通过 `[project.entry-points.bub]` group 暴露的 plugin 模型。kernel
有意保持小巧；所有有意思的东西都是 plugin。

`agentseek` 这个 harness 包把该 kernel 打包成 "在真实 workspace 中运行的真实项目"。这意味着
opinionated 的默认设置（数据放在哪里、变量长什么样、install sandbox 叫什么名字、捆绑了哪些
skill），以及 CLI 的品牌。这并不意味着替换、扩展或隐藏 Bub：`agentseek` 把 Bub 作为普通 distribution 依赖
（`pyproject.toml:19`，`bub>=0.3.7`），CLI 是在 agentseek 专属的 override 应用后，由
`BubFramework.create_cli_app()` 创建的（`src/agentseek/__main__.py:52-69`）。

## 工作原理

### 启动顺序

当你运行 `agentseek …` 时，entry point 会按顺序做三件事
（`src/agentseek/__main__.py:18-19`）：

1. `apply_agentseek_env_aliases()` —— 把 `AGENTSEEK_*` 的值复制到对应的 `BUB_*` 名称下，
   这样栈中其余部分就只从一个前缀读取配置。
2. `apply_agentseek_runtime_overrides()` —— 重新品牌 onboard banner，替换 chat 命令以启用
   lifecycle channel，调整 plugin-install 默认值，并直接解析 AgentSeek package requirement。
3. `create_cli_app()` 实例化 `BubFramework(config_file=agentseek_config_file())` 并向它请求
   一个 Typer app。从这一刻起，runtime 就是普通的 Bub。

Docker entrypoint 同理（`entrypoint.sh:5-45`）：它解析 `BUB_*`/`AGENTSEEK_*` 配对，
导出两者，然后在 `${workspace_path}/startup.sh` 存在时 exec 它，否则回退到
`agentseek gateway`。

### Alias 映射

alias 规则位于
`src/agentseek/env.py:56-65`（`apply_agentseek_env_aliases`）和
`src/agentseek/env.py:105-114`（`_bub_aliases`）：

- 对于进程环境或本地 `.env` 文件中名字以 `AGENTSEEK_` 开头且值非空的每个变量，
  agentseek 会**将** `BUB_<suffix>` 设为相同的值，**当且仅当 `BUB_<suffix>` 尚未设置时**
  （`setdefault` 语义，line 64）。
- 因此预先存在的 `BUB_*` 变量会胜过 `AGENTSEEK_*` alias。这就是 contrib README 也提到的
  "BUB 优先" 规则
  （[contrib/](https://github.com/ob-labs/agentseek/tree/main/contrib)）。

此外，当缺失时有两个位置默认值会被无条件应用
（`src/agentseek/env.py:68-73`）：

| 变量 | 未设置时的默认值 | 来源 |
| --- | --- | --- |
| `BUB_HOME` | `${cwd}/.agentseek` | `src/agentseek/env.py:15`（`DEFAULT_AGENTSEEK_HOME`）和 `src/agentseek/env.py:86-88` |
| `BUB_PROJECT` | `${BUB_HOME}/agentseek-project` | `src/agentseek/env.py:22`（`DEFAULT_PLUGIN_SANDBOX`）和 `src/agentseek/env.py:70-73` |

完整的逐变量表 —— 包括 model、API key、MCP path、skills home、workspace ——
位于 [环境变量参考](../reference/environment.zh.md)。

### CLI override

CLI 从 Bub app 出发，然后 AgentSeek 叠加一层小的命令布局：

- onboarding banner 读作 `AGENTSEEK` 而不是 `BUB`
  （`src/agentseek/cli.py:23-32`、`74-80`）。流程上没有变化。
- `chat` 被替换，让 lifecycle channel（`*.lifecycle`）与 `cli` 一同启用
  （`src/agentseek/cli.py:83-112`）。这就是让 MCP 等 helper 能在 CLI chat 会话中启动的机制。
- `plugin install` 通过用 `_ensure_plugin_sandbox` 替换 `_ensure_project`，将一个全新的 plugin sandbox
  解析到 `.agentseek/agentseek-project` 下，而不是 Bub 的 `bub-project`
  （`src/agentseek/cli.py:115-140`）。如果目录不存在，按需执行 `uv init --bare --name agentseek-project`。
- Bub 的根级 `run` 命令在 AgentSeek 中暴露为 `agentseek turn`。
- Bub 的根级 plugin 变更命令收敛到 `agentseek plugin` 下。

项目生命周期命令由 `src/agentseek/lifecycle/app.py` 挂载；运行时行为仍然流经 Bub。

## 为什么是这样

- **默认值属于 distribution，不属于 kernel。** Bub 保持通用；agentseek 拥有 "项目 workspace
  长什么样" 的决策权。其他 distribution 可以做出不同选择，而不必触碰 Bub。
- **Alias 是单向的，且 BUB 优先。** Plugin 作者可以面向上游前缀编写代码，在 agentseek 下也能干净
  运行，因为 alias 只填空。这就是为什么 contrib README 告诉 plugin 作者只把 `AGENTSEEK_*`
  保留给 distribution 范围的设置，让 `BUB_*` 主导 runtime 行为
  （[contrib/](https://github.com/ob-labs/agentseek/tree/main/contrib)）。
- **没有 Bub 的私有 fork。** Bub 是一个普通依赖，在 `pyproject.toml:19` 中按版本固定。升级 Bub
  就升级 agentseek；agentseek 中除了上面三处 Typer monkeypatch 外，没有任何代码 vendor 或
  patch 这个 kernel。

## 对用户的影响

- Debug 时可以对比 `uv run bub --help` 和 `uv run agentseek --help`，但两者命令面并不刻意相同。
  AgentSeek 增加生命周期命令组，并规范化有歧义的根命令。
- 不论你在 `AGENTSEEK_*` 中放什么，在进程持续期间都会渗入 `BUB_*`，除非 `BUB_*` 已经被设置。
  当你 debug 一个只记录了 `BUB_*` 名称的 plugin 时，这一点很重要。
- alias 层应用的默认值（`.agentseek` home、`agentseek-project` sandbox）会在你在一个 workspace
  中首次运行任何 `agentseek` 命令时显现出来。偏好系统级布局的运维人员应该显式设置 `BUB_HOME`
  和 `BUB_PROJECT`。
- 如果某个问题在 `agentseek` 下能复现但在 `bub` 下不能，嫌疑目标就是
  `src/agentseek/cli.py` 中的 override，或 `src/agentseek/env.py:56` 中的
  alias 步骤。通过直接用 `bub` 跑同一条命令来二分定位。

## 何时直接使用 `bub`

在以下情况下伸手去拿上游 CLI：

- 你想**精确复现 Bub Hub** (<https://hub.bub.build>) 中文档里的示例。
- 你正在**开发一个 Bub plugin**，想确保它不会悄悄依赖 agentseek 的默认值 —— 用 `bub` 配合上游
  sandbox 和 Bub 前缀的环境变量运行它。
- 你**不希望 workspace 中出现 project-local 的 `.agentseek/` 目录**，更愿意自己管理 `BUB_HOME`，
  例如在多租户容器中。
- 你在诊断一个 bug 究竟出在 Bub 还是出在 agentseek 的 override 里。

当你想要 opinionated 默认值时使用 `agentseek`：一个 workspace-local 的 home、agentseek
plugin install sandbox、chat 模式下的 lifecycle channel、生命周期命令组，以及 `AGENTSEEK_*` 命名。

## 相关

- 教程：[02 —— 构建你的第一个 harness 应用](../tutorials/02-first-harness-app.zh.md)
- 操作指南：[如何安装插件](../how-to/install-a-plugin.zh.md),
  [如何配置模型提供商](../how-to/configure-model.zh.md)
- 参考：[环境变量参考](../reference/environment.zh.md),
  [CLI 参考](../reference/cli.zh.md)
- 概念解释：[运行时数据模型](runtime-data-model.zh.md)
- 外部：[Bub repository](https://github.com/bubbuild/bub),
  [Bub Hub](https://hub.bub.build),
  [Why we rewrote Bub](https://bub.build/posts/why-rewrite-bub/)
