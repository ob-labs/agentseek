---
title: 各样东西的位置
type: explanation
audience: [A2, A3, A4, A5]
runs: no
verified_on: 2026-06-08
sources:
  - README.md
  - pyproject.toml
  - contrib/README.md
---

# 各样东西的位置

AgentSeek 是一个 uv workspace。核心包代码在 `src/`，可选集成在 `contrib/`，
项目模板在 `templates/`，可运行示例在 `examples/`，文档在 `docs/`。

```text
agentseek/
├── src/
│   ├── agentseek/        ← 主包：runtime、CLI、项目命令
│   └── skills/           ← 打进 wheel 的内置 skills
├── contrib/              ← 可选 runtime 集成包
├── examples/             ← 可运行端到端示例
├── templates/            ← `agentseek create` 使用的 Cookiecutter 源
├── skills/               ← 随项目维护的 standalone skills
├── references/           ← 供阅读的上游源码快照
├── docs/                 ← 发布文档
├── tests/                ← 顶层测试
├── entrypoint.sh         ← Docker entrypoint
├── docker-compose.yml    ← Compose 定义
└── pyproject.toml        ← package、依赖和 workspace 的事实来源
```

## `src/agentseek`

发布到 PyPI 的 `agentseek` 包。它包含：

- runtime 默认值和 `AGENTSEEK_*` 别名；
- 对 Bub 命令的 CLI 布局规范化；
- 位于 `src/agentseek/cli` 的项目命令；
- 公开 `agentseek` console entry point。

## `contrib`

通过 Bub entry point 扩展 runtime 或提供 framework / storage 集成的可选包。每个包维护自己的
README、测试和配置参考。

## `templates`

`agentseek create` 使用的 Cookiecutter 源。模板可以生成 Bub、LangChain 或 DeepAgents 项目；
根据目的不同，有些依赖 AgentSeek，有些保持自包含。

## `skills`

`src/skills` 是随 wheel 发布的内置 skills；顶层 `skills/` 是随项目维护的 standalone skills。

## `references`

只读的上游源码快照，用于本地阅读和搜索，不是依赖。

## 判断规则

### `examples/` —— 可运行的端到端 demo

故意位于包源代码树之外，这样每个示例都展示用户 workspace 的安装 + 运行形态。
今天的目录（来自 [examples/](https://github.com/ob-labs/agentseek/tree/main/examples)）是
`agentseek_api_remote_agent` 和 `langchain_otel_sidecar`。当你想要看整套组装 ——
gateway + 前端 + LangChain + agentseek —— 而不是只看 harness 时，它们是正确的起点。
其他常见模式（AG-UI、LangChain 默认、CLI remote、DeepAgents）已被 `agentseek create`
模板覆盖。

### `templates/` —— 项目脚手架

`agentseek create` 使用的 Cookiecutter 源。目录位于 `templates/index.json`：

| 模板 | 用途 |
| --- | --- |
| `bub/default` | 轻量 Bub agent：`agentseek gateway` + CopilotKit 前端，不带 LangChain。 |
| `langchain/default` | LangChain `create_agent` + CopilotKit 中间件，基于 `agentseek-langchain`。 |
| `langchain/cli-remote` | 远端 LangGraph CLI agent，通过 `LangGraphClientRunnable` 桥接。 |
| `deepagents/default` | 本地 `create_deep_agent` runnable，绑定到 `agentseek-langchain`。 |

由于文件包含 Jinja2 占位符而非真正的 Python，该目录在 ty（`pyproject.toml:111-117`）和 ruff
（`pyproject.toml:124-130`）中都被排除。参考：[模板参考](../reference/templates.zh.md)。

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
  见 [命令概览](cli-surface.zh.md)。
- `pyproject.toml` 是 distribution、依赖和 workspace 成员列表的事实来源。

## 为什么是这样

- **一个包，一个 CLI。** 发布的 harness 包（`agentseek`）同时拥有 runtime、公开 CLI
  入口和项目命令。contrib plugin 仍可按自己的节奏演进，并通过
  `agentseek plugin install <package>` 安装。
- **捆绑 vs project-local skill。** 把 skill 捆绑进 wheel 让它们可重现（`src/skills/`）；
  workspace-local skill（`.agents/skills/`）让它们可被 hack。独立的 skill repo
  （`skills/`）介于两者之间，适合应该按需安装的 skill。
- **示例位于包之外。** 把示例保留在 `examples/` 而非某个包下面，展示了队友实际会用的安装形态 ——
  plugin 安装好、gateway 启动、前端串好。
- **References 是 check in 的，不是 vendor 的。** 它们是搜索目标，不是依赖。这种权衡保持
  grep 廉价而不承担维护负担。

## 代码应该放在哪里

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

- [包参考](../reference/packages.zh.md)
- [文件布局参考](../reference/file-layout.zh.md)
- [命令概览](cli-surface.zh.md)
