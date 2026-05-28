---
title: 包参考
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - pyproject.toml
  - contrib/README.md
---

# 包参考

发行版布局、可选 extras、contrib 入口点以及 uv workspace 成员。本页所有事实均镜像
验证日期的 `pyproject.toml`。

## 发行版

| 字段 | 值 | 来源 |
| --- | --- | --- |
| Name | `agentseek` | `pyproject.toml:2` |
| Version | `0.1.0` | `pyproject.toml:3` |
| Python | `>=3.12,<4.0` | `pyproject.toml:8` |
| Console script | `agentseek = "agentseek.__main__:app"` | `pyproject.toml:49` |
| Build backend | `pdm.backend`（`pdm-backend`、`pdm-build-skills>=0.1.0a3`） | `pyproject.toml:69` |
| Build includes | `src/agentseek`、`src/skills` | `pyproject.toml:74` |

## 核心依赖

| 包 | 约束 | 来源 pin |
| --- | --- | --- |
| `bub` | `>=0.3.7` | PyPI |
| `bub-feishu` | （无版本） | `git+bub-contrib@5374c8f`（`pyproject.toml:89`） |
| `bub-mcp` | （无版本） | `git+bub-contrib@5374c8f`（`pyproject.toml:90`） |
| `agentseek-schedule-sqlalchemy` | （无版本） | workspace |
| `logfire` | `>=4.33.0` | PyPI |
| `pydantic-settings` | `>=2.0.0` | PyPI |

## 可选 extras

定义于 `pyproject.toml:27`。通过 `uv pip install 'agentseek[<extra>]'` 或
`uv sync --extra <extra>` 安装。

| Extra | 拉入 | 用途 |
| --- | --- | --- |
| `ag-ui` | `agentseek-ag-ui` | AG-UI 适配器与 FastAPI helpers。 |
| `cli` | `agentseek-cli` | 项目生命周期 CLI（`create / run / build / deploy / api / ctx / skills`）。 |
| `langchain` | `agentseek-langchain` | LangChain `Runnable` / agent 桥接。 |
| `observability` | `agentseek-observability` | Logfire 支持的 spans。 |
| `oceanbase` | `agentseek-tapestore-oceanbase` | 兼容 OceanBase 的 SQLAlchemy tape 存储。 |
| `context` | `agentseek-cli`、`agentseek-contextseek` | ContextSeek 语义上下文运行时 plugin（同时带入 `agentseek ctx` 所需的 CLI）。 |

## Contrib 包

Workspace 成员位于 `contrib/` 下（`pyproject.toml:101`）。每个都有自己的 README；
不要在此处重复配置。

| 发行版 | Bub 入口点 | Workspace 路径 | README |
| --- | --- | --- | --- |
| `agentseek-ag-ui` | n/a | `contrib/agentseek-ag-ui` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-ag-ui/README.md) |
| `agentseek-cli` | `cli` | `contrib/agentseek-cli` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-cli/README.md) |
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

- 操作指南：`../how-to/install-a-plugin.md`、
  `../how-to/author-a-contrib-plugin.md`
- 参考：`cli.md`、`file-layout.md`
