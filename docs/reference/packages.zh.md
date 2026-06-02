---
title: 包参考
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-29
sources:
  - pyproject.toml
  - contrib/agentseek-cli/pyproject.toml
  - contrib/README.md
---

# 包参考

包布局、可选 extras、contrib 入口点以及 uv workspace 成员。本页所有事实均镜像
验证日期的 `pyproject.toml`。

## 两个顶层 PyPI 包

agentseek 在 PyPI 上以**两个互补的包**形式提供，按职责拆分。两者都注册了同一个
名为 `agentseek` 的 console script；`agentseek …` 在当前环境里能做什么，取决于
哪一个包是活跃的。

| 包 | 角色 | 源码 | Console script | 安装方式 |
| --- | --- | --- | --- | --- |
| `agentseek` | Harness —— 运行时 CLI 与可嵌入的库（`chat`、`run`、`gateway`、`install`、`update`、…） | `pyproject.toml:2`、`src/agentseek/` | `agentseek = "agentseek.__main__:app"`（`pyproject.toml:49`） | **不能直接从 PyPI 安装。** 请在本仓库执行 `git clone … && uv sync`，或在 `agentseek create` 生成的项目里执行 `uv sync`。 |
| `agentseek-cli` | 项目生命周期 CLI（`create`、`run`、`build`、`deploy`、`api`、`ctx`、`skills`） | `contrib/agentseek-cli/pyproject.toml:2`、`contrib/agentseek-cli/src/agentseek_cli/` | `agentseek = "agentseek_cli.standalone:app"`（`contrib/agentseek-cli/pyproject.toml:18`） | `uv tool install agentseek-cli`（首选），或在本仓库内以 `cli` extra 拉入 |

> **为什么 `agentseek` 不能从 PyPI 直装** —— 它的 `requires-dist` 包含
> `bub-feishu`、`bub-mcp` 与 `agentseek-schedule-sqlalchemy`。这些依赖通过本
> 仓库的 `[tool.uv.sources]` 接到 git source / workspace，PyPI metadata 无法
> 携带 source 覆盖。直接 `pip install agentseek` 或 `uv tool install agentseek`
> 都会解析失败。可靠的路径是路径 B（`git clone + uv sync`）或路径 A
> （`uv tool install agentseek-cli` → `agentseek create` → 在生成的项目里
> `uv sync`），二者都自带 `[tool.uv.sources]`。参见
> [agentseek](../index.zh.md)。

### `agentseek`（harness）

| 字段 | 值 | 来源 |
| --- | --- | --- |
| Name | `agentseek` | `pyproject.toml:2` |
| Version | `0.1.0` | `pyproject.toml:3` |
| Python | `>=3.12,<4.0` | `pyproject.toml:8` |
| Build backend | `pdm.backend`（`pdm-backend`、`pdm-build-skills>=0.1.0a3`） | `pyproject.toml:69` |
| Build includes | `src/agentseek`、`src/skills` | `pyproject.toml:74` |

### `agentseek-cli`（项目生命周期 CLI）

| 字段 | 值 | 来源 |
| --- | --- | --- |
| Name | `agentseek-cli` | `contrib/agentseek-cli/pyproject.toml:2` |
| Version | `0.1.0` | `contrib/agentseek-cli/pyproject.toml:3` |
| Python | `>=3.12` | `contrib/agentseek-cli/pyproject.toml:7` |
| Console script | `agentseek = "agentseek_cli.standalone:app"` | `contrib/agentseek-cli/pyproject.toml:18` |
| Bub 入口点 | `cli = "agentseek_cli.plugin:main"` | `contrib/agentseek-cli/pyproject.toml:21` |
| Build backend | `pdm.backend` | `contrib/agentseek-cli/pyproject.toml:24` |

`project.scripts` 与 `entry-points.bub` 的双重注册，使得同一个包能在路径 A
作为独立 CLI 运行，在路径 B 作为运行时 plugin 折叠进 `agentseek …`。各模式
下的命令面详见 [CLI 参考](cli.zh.md)。

## Harness 核心依赖

以下是 `agentseek` 包的 `requires-dist`（`pyproject.toml:18`）：

| 包 | 约束 | 来源 pin |
| --- | --- | --- |
| `bub` | `>=0.3.7` | PyPI |
| `bub-feishu` | （无版本） | `git+bub-contrib@5374c8f`（`pyproject.toml:89`） |
| `bub-mcp` | （无版本） | `git+bub-contrib@5374c8f`（`pyproject.toml:90`） |
| `agentseek-schedule-sqlalchemy` | （无版本） | workspace |
| `logfire` | `>=4.33.0` | PyPI |
| `pydantic-settings` | `>=2.0.0` | PyPI |

`bub-feishu`、`bub-mcp` 与 `agentseek-schedule-sqlalchemy` **都不在 PyPI 上**。
这正是上面"agentseek 不能从 PyPI 直装"提示的根因。

## 安装插件

插件通过 `agentseek install` 命令安装。之前的 `[optional-dependencies]` extras
（例如 `pip install agentseek[langchain]`）已被移除；只有 `agentseek[cli]` 作为
pip extra 保留。

> `cli` extra **不是**拿到项目生命周期 CLI 的唯一途径；
> `uv tool install agentseek-cli` 同样能独立安装该包。

| 插件包 | 安装命令 | 用途 |
| --- | --- | --- |
| `agentseek-ag-ui` | `agentseek install agentseek-ag-ui` | AG-UI 适配器与 FastAPI helpers。 |
| `agentseek-cli` | `agentseek install agentseek-cli` 或 `uv tool install agentseek-cli` | 把项目生命周期 CLI 合并进 harness 环境（`create / run / build / deploy / api / ctx / skills`）。 |
| `agentseek-langchain` | `agentseek install agentseek-langchain` | LangChain `Runnable` / agent 桥接。 |
| `agentseek-observability` | `agentseek install agentseek-observability` | Logfire 支持的 spans。 |
| `agentseek-tapestore-oceanbase` | `agentseek install agentseek-tapestore-oceanbase` | 兼容 OceanBase 的 SQLAlchemy tape 存储。 |
| `agentseek-contextseek` | `agentseek install agentseek-contextseek` | ContextSeek 语义上下文运行时 plugin（同时带入 `agentseek ctx` 所需的项目生命周期 CLI）。 |

## Contrib 包

Workspace 成员位于 `contrib/` 下（`pyproject.toml:101`）。每个都有自己的 README；
不要在此处重复配置。

`agentseek-cli` 也出现在此表中，但它本身是一个独立的顶层 PyPI 包（参见本页顶部
表格），不是像其它行那样的运行时 plugin。

| 包 | Bub 入口点 | Workspace 路径 | README |
| --- | --- | --- | --- |
| `agentseek-cli`（项目生命周期 CLI） | `cli` | `contrib/agentseek-cli` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-cli/README.md) |
| `agentseek-ag-ui` | n/a | `contrib/agentseek-ag-ui` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-ag-ui/README.md) |
| `agentseek-langchain` | `langchain` | `contrib/agentseek-langchain` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-langchain/README.md) |
| `agentseek-observability` | `observability` | `contrib/agentseek-observability` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-observability/README.md) |
| `agentseek-tapestore-oceanbase` | `tapestore-oceanbase` | `contrib/agentseek-tapestore-oceanbase` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-tapestore-oceanbase/README.md) |
| `agentseek-schedule-sqlalchemy` | `schedule` | `contrib/agentseek-schedule-sqlalchemy` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-schedule-sqlalchemy/README.md) |
| `agentseek-contextseek` | `contextseek` | `contrib/agentseek-contextseek` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md) |

入口点由每个 contrib 包在 `[project.entry-points.bub]` 下声明。Bub 入口点这一列
复现自 `contrib/README.md`。

## uv 工作区成员

```text
contrib/agentseek-ag-ui
contrib/agentseek-cli
contrib/agentseek-langchain
contrib/agentseek-observability
contrib/agentseek-schedule-sqlalchemy
contrib/agentseek-tapestore-oceanbase
contrib/agentseek-contextseek
.agentseek/agentseek-project
```

末尾的 `.agentseek/agentseek-project` 是 **默认 plugin sandbox**；将其作为 workspace
成员，可以让 uv 针对同一 lockfile 解析由 `agentseek install` 安装的 plugins
（`pyproject.toml:109`）。

## 构建时捆绑的 skills

`[tool.pdm.build].skills`（`pyproject.toml:78`）：

| 来源 | 子路径 | 包含的 skills |
| --- | --- | --- |
| `git+https://github.com/PsiACE/skills.git` | `skills` | `friendly-python`、`piglet` |

它们随 wheel 一起发布，位于顶层 `skills/` 包下，与项目自身 `src/skills/` 内容并存。

## Index URL

`[tool.uv]` 将 `index-url = "https://pypi.org/simple"` 固定下来
（`pyproject.toml:85`）。为加快开发安装速度，可以将 `UV_INDEX_URL` 设为镜像
（例如 `https://pypi.tuna.tsinghua.edu.cn/simple`）。

## 另请参阅

- 概览：[agentseek](../index.zh.md)
- 概念解释：[选择一个入口](../explanation/choosing-an-entry-point.zh.md)
- 操作指南：[如何安装插件](../how-to/install-a-plugin.zh.md)、
  [如何编写 contrib 插件](../how-to/author-a-contrib-plugin.zh.md)
- 参考：[CLI 参考](cli.zh.md)、[文件布局参考](file-layout.zh.md)
