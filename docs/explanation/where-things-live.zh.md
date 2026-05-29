---
title: monorepo 中各样东西的位置
type: explanation
audience: [A2, A3, A4, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - docs/index.md
  - pyproject.toml
  - contrib/agentseek-cli/pyproject.toml
  - contrib/README.md
  - examples/README.md
  - src/skills/README.md
  - skills/README.md
  - docs/hub.md
---

# monorepo 中各样东西的位置

> **简而言之：** agentseek repository 是一个 uv workspace，并在其中发布两个顶层包：
> `agentseek`（harness）与 `agentseek-cli`（项目生命周期 CLI）。核心代码位于 `src/`，
> 更大的集成位于 `contrib/`，可运行的端到端 demo 位于 `examples/`，项目脚手架位于
> `templates/`，配套的 skill repo 位于 `skills/`，vendor 进来的上游代码位于
> `references/`，发布的文档位于 `docs/`。

## 背景

agentseek 有意是一个 monorepo：harness、捆绑的 plugin、contrib 集成、示例和文档一同演进。
目录名看起来很熟悉，但每一个都有特定角色；把它们搞混是新贡献者把文件放错位置的最常见原因。

本页是带注释的地图。要获取确切的安装命令和 entry point，请跳到引用的 README，而不是从头到尾
读这一页。

## 工作原理

```text
agentseek/
├── src/
│   ├── agentseek/        ← harness 包（PyPI: agentseek）
│   └── skills/           ← 随 wheel 一起发布的捆绑 skill
├── contrib/
│   ├── README.md         ← contrib README 标准与包索引
│   ├── agentseek-cli/    ← 项目生命周期 CLI（PyPI: agentseek-cli）
│   └── agentseek-*/      ← 运行时 plugin 包（workspace 成员）
├── examples/             ← 可运行的端到端 demo
├── templates/            ← `agentseek create` 使用的项目脚手架
├── skills/               ← 独立 skill，独立于 `src/skills`
├── references/           ← vendor 进来的上游源，仅供阅读
├── docs/                 ← 发布文档（Diátaxis：tutorials/how-to/reference/explanation）
├── scripts/              ← 项目脚本（目前为空）
├── tests/                ← 顶层测试
├── entrypoint.sh         ← Docker entrypoint
├── docker-compose.yml    ← Compose 定义
├── pyproject.toml        ← harness pyproject（依赖、extras、workspace 成员）
└── README.md             ← 仓库 README；项目入口
```

### `src/agentseek/` —— harness 包

发布到 PyPI 时名为 `agentseek`（harness 本身）的 Python 包。它**不能**直接
从 PyPI 安装：`requires-dist` 包含 `bub-feishu`、`bub-mcp`、
`agentseek-schedule-sqlalchemy`，这些依赖通过 `[tool.uv.sources]` 接到 git
source / workspace；PyPI metadata 无法携带 source 覆盖，因此
`pip install agentseek` 与 `uv tool install agentseek` 都会失败。请克隆本仓库后
`uv sync`，或在 `agentseek create` 生成的项目里 `uv sync`。详见
[选择一个入口](choosing-an-entry-point.zh.md)。

三个文件重要：

- `src/agentseek/env.py` —— `AGENTSEEK_*` 到 `BUB_*` 的 alias 规则，加上位置默认值
  （`.agentseek/`、`.agentseek/agentseek-project`）。机制在
  [agentseek 与 Bub 的关系](bub-relationship.zh.md) 中解释。
- `src/agentseek/cli.py` —— 给 onboarding 加品牌、在 `chat` 中启用 lifecycle channel，
  以及重新指向 install sandbox 的三处 Typer monkeypatch。
- `src/agentseek/__main__.py` —— 跑 alias 步骤、应用 CLI override 并构造 `BubFramework`
  的启动顺序。

这是 core harness 代码唯一存在的地方。任何更大的东西都进入 `contrib/`。

### `src/skills/` —— 捆绑的 skill

由于 `pyproject.toml:73-77` 将 `src/skills` 包含进 build，因此在 distribution 内部发布的 skill。
撰写本文时该目录包含 `plugin-creator/`，加上通过 `[tool.pdm.build].skills` 在 build 时从外部
repo 导入的 skill（`pyproject.toml:78-80`）—— 当前是来自
<https://github.com/PsiACE/skills> 的 `friendly-python` 和 `piglet`。
捆绑 skill 列表见 [src/skills/](https://github.com/ob-labs/agentseek/tree/main/src/skills)；
关于 skill 是什么，见 [运行时数据模型](runtime-data-model.zh.md)。

### `contrib/` —— 较大的集成

Workspace member 包，每一个都是一个带自己 README 的常规 Python 包。索引和 README
标准位于 [contrib/](https://github.com/ob-labs/agentseek/tree/main/contrib)。
`agentseek-cli` 自己也是一个顶层 PyPI 包（路径 A 的项目生命周期 CLI ——
见 [选择一个入口](choosing-an-entry-point.zh.md)），其余项是 harness 的运行时 plugin。

| 目录 | 角色 | 用途 |
| --- | --- | --- |
| `agentseek-cli` | **项目生命周期 CLI**（顶层 PyPI 包） | `create / run / build / deploy / api / ctx / skills`。通过 `uv tool install agentseek-cli` 安装；与 harness 共存时会折叠进同一个 `agentseek` 命令面。 |
| `agentseek-ag-ui` | 运行时 plugin | 为 `agentseek gateway` 提供 AG-UI SSE channel 适配器。 |
| `agentseek-contextseek` | 运行时 plugin | ContextSeek 语义 context 层。 |
| `agentseek-langchain` | 运行时 plugin | 把 Bub model turn 路由到用户提供的 LangChain `Runnable`。 |
| `agentseek-observability` | 运行时 plugin | 跨 any-llm / Republic / Bub 栈的 Logfire 支撑 tracing。 |
| `agentseek-schedule-sqlalchemy` | 运行时 plugin（作为 harness 硬依赖捆绑） | SQLAlchemy 支撑的 APScheduler job store。 |
| `agentseek-tapestore-oceanbase` | 运行时 plugin | SQLAlchemy tape 存储，兼容 OceanBase。 |

每个包拥有自己的安装、配置、运行和验证文档。主文档链接出去；它们不重复。workspace 映射位于
`pyproject.toml:100-110`。

### `examples/` —— 可运行的端到端 demo

故意位于包源代码树之外，这样每个示例都展示用户 workspace 的安装 + 运行形态。
今天的目录（来自 [examples/](https://github.com/ob-labs/agentseek/tree/main/examples)）是
`ag-ui`、`ag_ui_langchain`、`agentseek_api_remote_agent`、`langchain_otel_sidecar`、
`langchain_deepagents` 和 `langchain_cli_remote_agent`。当你想要看整套组装 ——
gateway + 前端 + LangChain + agentseek —— 而不是只看 harness 时，它们是正确的起点。

### `templates/` —— 项目脚手架

`agentseek create`（由 `agentseek-cli` 提供）使用的 Cookiecutter 源。目录位于
`templates/index.json`：

| 模板 | 用途 |
| --- | --- |
| `bub/default` | 轻量 Bub agent：`agentseek gateway` + CopilotKit 前端，不带 LangChain。 |
| `langchain/default` | LangChain `create_agent` + CopilotKit 中间件，基于 `agentseek-langchain`。 |
| `langchain/cli-remote` | 远端 LangGraph CLI agent，通过 `LangGraphClientRunnable` 桥接。 |
| `deepagents/default` | 本地 `create_deep_agent` runnable，绑定到 `agentseek-langchain`。 |

由于文件包含 Jinja2 占位符而非真正的 Python，该目录在 ty（`pyproject.toml:120-126`）和 ruff
（`pyproject.toml:133-139`）中都被排除。参考：[模板参考](../reference/templates.zh.md)。

### `skills/` —— 独立的 skill repository

与 `src/skills/` 分开。本目录保存那些与项目一同维护、但 **不捆绑进 `agentseek` wheel** 的
skill。今天的条目是 `github-repo-cards` 和 `langchain-cn-models`；目录见
[skills/](https://github.com/ob-labs/agentseek/tree/main/skills) 和发布的
[Hub 页面](../hub.zh.md)。通过 `npx skills add` 或复制文件夹，把它们安装到你的 workspace
下的 `.agents/skills/`。

### `references/` —— vendor 进来的上游源

为离线导航和 grep 目标而 check in 的上游项目只读副本：
`agentseek-api`、`ag-ui`、`bub`、`bub-contrib`、`buildscape`、`logfire`、`republic`、
`wheels`。它们**不是**依赖。不要编辑；把它们当作搜索索引。

### `docs/`

`docs/` 保存发布的文档。Diátaxis 布局遵循四个象限
（[教程](../tutorials/index.zh.md)、[操作指南索引](../how-to/index.zh.md)、
[参考索引](../reference/index.zh.md)、[概念解释 -- 理解 agentseek](../explanation/index.zh.md)），
加上一个 `blog/` 归档和一个发布的 `hub.md` 浏览页。

通用的 Diátaxis 编写标准和四个页面模板位于 documentation-writer skill 中，路径为
`.agents/skills/documentation-writer/`。新文档页面进入 `docs/`，遵循该 skill 的约定。

`hub.md` 页面是为 plugin、skill 及伙伴发布的浏览表面；它是整个站点中用到的
navigation/where-things-live 图景的来源。

### `scripts/`、`tests/` 与顶层文件

- `scripts/` 保留给项目脚本，目前为空。
- `tests/` 保存顶层测试；contrib 包在 `contrib/*/tests/` 下有自己的测试树。
- `entrypoint.sh` 和 `docker-compose.yml` 是 Docker entry point；
  见 [选择一个入口](choosing-an-entry-point.zh.md)。
- `pyproject.toml` 是 distribution、可选 extras 和 workspace 成员列表的事实来源。

## 为什么是这样

- **两个包，一个 workspace。** uv workspace 让 harness（`agentseek`）和项目
  生命周期 CLI（`agentseek-cli`）以两个 PyPI 包形式发布，同时 contrib
  plugin 按自己的节奏演进。可选 extras（`pyproject.toml:27-46`）让在仓库内
  采用它们变成一行变更。
- **捆绑 vs project-local skill。** 把 skill 捆绑进 wheel 让它们可重现（`src/skills/`）；
  workspace-local skill（`.agents/skills/`）让它们可被 hack。独立的 skill repo
  （`skills/`）介于两者之间，适合应该按需安装的 skill。
- **示例位于包之外。** 把示例保留在 `examples/` 而非某个包下面，展示了队友实际会用的安装形态 ——
  extras 固定、gateway 启动、前端串好。
- **References 是 check in 的，不是 vendor 的。** 它们是搜索目标，不是依赖。这种权衡保持
  grep 廉价而不承担维护负担。

## 对用户的影响

- 在 `src/agentseek/` 下添加 core agentseek 代码。如果一个改动需要自己的依赖或测试面，
  它就是一个 contrib 包。
- 新 plugin 进入 `contrib/agentseek-<feature>/` 并从一开始就遵循
  [contrib/README.md](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md)
  的 README 标准。位于 `src/skills/plugin-creator/` 的捆绑 `plugin-creator` skill 会
  脚手架出布局。
- 新的端到端 demo 进入 `examples/`，而不是某个包下面。
- Skill 改动进入 `src/skills/`（捆绑）或 `.agents/skills/`（project-local）；
  `skills/` 留给独立维护的独立 repo。
- 新文档页面进入 `docs/<quadrant>/`，遵循 `.agents/skills/documentation-writer/SKILL.md`
  中 `documentation-writer` skill 的约定。

## 相关

- 操作指南：[如何安装插件](../how-to/install-a-plugin.zh.md),
  [如何添加 skill](../how-to/add-skills.zh.md),
  [如何编写 contrib 插件](../how-to/author-a-contrib-plugin.zh.md)
- 参考：[文件布局参考](../reference/file-layout.zh.md),
  [包参考](../reference/packages.zh.md),
  [模板参考](../reference/templates.zh.md)
- 概念解释：[扩展模型](extension-model.zh.md),
  [选择一个入口](choosing-an-entry-point.zh.md)
- 外部：[contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md),
  [examples catalogue](https://github.com/ob-labs/agentseek/tree/main/examples),
  [Hub 页面](../hub.zh.md)
