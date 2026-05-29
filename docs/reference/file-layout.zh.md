---
title: 文件布局参考
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/env.py
  - entrypoint.sh
  - pyproject.toml
  - docs/index.md
---

# 文件布局参考

本页描述的是 **harness 运行时布局**：也就是路径 B 在真正运行 `agentseek`
之后会创建和使用的目录。单独的路径 A（`uv tool install agentseek-cli`）
本身不会创建其中大部分路径，除非你进一步进入一个已同步 harness 的项目环境。

agentseek 在运行时会接触三个目录：**运行时 home**（Bub 状态、config、MCP）、
**workspace skills 目录**（`.agents/`），以及 **plugin sandbox**（一个保存已安装
Bub plugins 的 uv project）。

## 本地布局（不使用 Docker）

在未设置 `BUB_HOME` / `AGENTSEEK_HOME` 时，`apply_agentseek_env_aliases` 中的默认值生效：

```text
<cwd>/
  .agentseek/                      # AGENTSEEK_HOME / BUB_HOME
    config.yml                     # Bub config (written by `agentseek onboard`)
    mcp.json                       # MCP server definitions (read by bub-mcp)
    agentseek-project/             # AGENTSEEK_PROJECT / BUB_PROJECT
      pyproject.toml               # `uv init --bare --name agentseek-project --app`
      ...                          # plugins installed by `agentseek install`
  .agents/
    skills/                        # project-local skills (Bub discovers from here)
    mcp.json                       # optional alternate MCP path
  .env                             # loaded by AgentseekSettings
```

| 路径 | 默认值来源 | 说明 |
| --- | --- | --- |
| `.agentseek/` | `DEFAULT_AGENTSEEK_HOME`（`src/agentseek/env.py:15`） | `Path.cwd() / ".agentseek"`。 |
| `.agentseek/config.yml` | `DEFAULT_AGENTSEEK_CONFIG`（`src/agentseek/env.py:18`） | 由 Bub onboarding 写入。 |
| `.agentseek/mcp.json` | `BUB_HOME` 下的 `bub-mcp` 默认值 | 通过 `AGENTSEEK_MCP_CONFIG_PATH` 覆盖。 |
| `.agentseek/agentseek-project/` | `DEFAULT_PLUGIN_SANDBOX`（`src/agentseek/env.py:22`） | 由 `src/agentseek/cli.py:123` 中的 `_ensure_plugin_sandbox` 延迟初始化。 |
| `.agents/skills/` | `entrypoint.sh:7`（容器）以及 Bub workspace skill 惯例 | 本地运行直接读取；容器以 symlink 形式链接。 |

## 容器布局（Docker / Compose）

`docker-compose.yml` 将 `${AGENTSEEK_DOCKER_WORKSPACE:-.}` 挂载到 `/workspace`，
entrypoint 会固定下面的变量：

```text
/workspace/                        # AGENTSEEK_WORKSPACE_PATH
  .agentseek/                      # AGENTSEEK_HOME
    mcp.json                       # link target for source mcp.json
    agentseek-project/             # AGENTSEEK_PROJECT
  .agents/
    skills/                        # AGENTSEEK_SKILLS_HOME default
    mcp.json                       # source for /workspace/.agentseek/mcp.json link
  startup.sh                       # optional, runs instead of `agentseek gateway`
```

解析顺序参见 [Docker 参考](docker.zh.md)。

## Plugin sandbox 语义

`agentseek install` 会在 `AGENTSEEK_PROJECT` / `BUB_PROJECT` 所在目录内运行。
首次调用使用 `_ensure_plugin_sandbox`（`src/agentseek/cli.py:123`）：

1. 对 project 路径执行 `mkdir -p`。
2. 若 `pyproject.toml` 已存在，则不做其他动作。
3. 否则执行 `uv init --bare --name agentseek-project --app`，再执行
   `uv add --active --no-sync <bub-requirement>`。

该 sandbox 是一个普通的 uv 管理 Python project。你可以检查或编辑其 `pyproject.toml`
来查看安装了哪些 plugins。

默认 sandbox 的 basename 必须与 `uv init --name` 匹配
（`src/agentseek/env.py:22` 与 `src/agentseek/cli.py:134`）。

`agentseek install` 属于 harness 运行时 CLI。只装了 `agentseek-cli` 的路径 A
环境本身不会创建或管理这个 sandbox。

## 捆绑 skills（`src/skills`）

`pyproject.toml:73` 同时将 `src/agentseek` 与 `src/skills` 声明为构建包含项。
`[tool.pdm.build].skills` 额外在构建时从外部 `PsiACE/skills` 仓库导入选定的 skills
（`friendly-python`、`piglet`）。

| 表面 | 仓库中的路径 | 构建出的 wheel 中的路径 |
| --- | --- | --- |
| 发行代码 | `src/agentseek/` | `agentseek/` |
| 捆绑 skills | `src/skills/` | `skills/` |
| 外部 skills | 由 `pdm-build-skills` 在构建时解析 | 合并到 `skills/` 下 |

`.agents/skills/<name>/` 下的 project skills **不**会打包 — 它们位于用户的 workspace 中。

## 另请参阅

- 操作指南：[如何安装插件](../how-to/install-a-plugin.zh.md)、[如何添加 skill](../how-to/add-skills.zh.md)
- 参考：[环境变量参考](environment.zh.md)、[Docker 参考](docker.zh.md)、[包参考](packages.zh.md)
