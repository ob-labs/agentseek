# agentseek

中文 | [English](README.md)

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

一个由 [OceanBase](https://www.oceanbase.com/) OSS Team 提供的数据库原生 Agent Harness。

## agentseek 是什么

agentseek 是一个面向团队的数据库原生 Agent Harness，适合那些希望把 agent 运行时数据变成一等数据库工作负载的场景。

它把数据库视为承载 agent 上下文、执行历史、工具调用、任务、反馈和观测数据的自然位置。这样，同一份运行时数据就可以直接服务于调试、回放、轨迹对比、评估、分析和训练工作流，而不需要复制到多个系统中，也不需要事后重新导入。

agentseek 在 PyPI 上以两个互补的包形式提供，按职责拆分：

- **`agentseek-cli`** —— **项目生命周期 CLI**（`create`、`run`、`build`、`deploy`、`api`、`ctx`、`skills`）。自包含，使用 `uv tool install agentseek-cli` 安装。
- **`agentseek`** —— **harness** 本身。提供运行时 CLI（`chat`、`run`、`gateway`、`install`、`update`、…）以及嵌入到你应用里的库。harness 通过本仓库的 `[tool.uv.sources]` 解析，**不能**直接 `pip install agentseek`。

两者都注册同一个名为 `agentseek` 的命令。要选哪一个，见 [`docs/index.zh.md`](docs/index.zh.md) 与 [`docs/explanation/choosing-an-entry-point.zh.md`](docs/explanation/choosing-an-entry-point.zh.md)。

## 为什么存在

大多数 agent 的价值都体现在运行时，但它们的运行时数据往往散落在 JSONL 日志、Markdown 笔记、SQLite 文件、tracing 系统、对象存储和离线流水线之间。第一次交互之后，这些数据再想查询、回放、比较、评估或转成训练材料，成本就会迅速上升。

agentseek 从另一个前提出发：上下文、记忆、任务、工具调用、trace、反馈和评估材料，从一开始就应该共享同一个持久化底座。对 agent 系统来说，这让运行时数据具备复用价值；对数据库来说，这意味着它不再只存放最终业务结果，而是可以直接承载智能应用的工作负载。

## 快速开始

两条入门路径都正式平等，按你的目的二选一。

### 路径 A —— 安装项目生命周期 CLI

需要生成项目、构建镜像、调用生命周期命令但不想把仓库克隆下来时，走这条。

```bash
uv tool install agentseek-cli
agentseek --help            # create / run / build / deploy / api / ctx / skills
agentseek create bub --template default --no-input
cd my_bub_agent
uv sync                     # 生成项目内部的 [tool.uv.sources] 会解析出完整 harness
```

### 路径 B —— 克隆仓库，运行 harness

需要驱动 harness 本体 —— `chat`、`gateway`、`install` 等运行时命令 —— 时走这条。

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help     # chat / run / gateway / install / update / …
```

配置一个模型，然后启动本地 chat：

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
uv run agentseek chat
```

> 注意：`pip install agentseek` 与 `uv tool install agentseek` 都会因为 harness 依赖 `bub-feishu`、`bub-mcp` 与 `contrib/` 下的 workspace 包而解析失败 —— 这些依赖通过 `[tool.uv.sources]` 接到 git source，PyPI 元数据无法携带。请使用上面两条路径之一。

## Docker Compose

如果你想在容器里运行 `agentseek`，并把项目工作区挂载进去，可以直接使用仓库自带的 compose 配置：

```bash
cp .env.example .env
make compose-up
```

默认情况下，compose 会：

- 把当前仓库挂载到 `/workspace`
- 复用 `.agents/skills` 和 `.agents/mcp.json`
- 把运行时状态持久化到工作区下的 `.agentseek`

如果你希望挂载其他宿主机目录作为工作区，请设置 `AGENTSEEK_DOCKER_WORKSPACE`。如果你想覆盖容器中的 MCP 配置源路径，请设置 `AGENTSEEK_MCP_CONFIG_PATH`。

## 文档

主文档描述的是 agentseek 内置发行版这一层：

- [Overview](docs/index.zh.md)：说明 agentseek 是什么、处在什么位置，以及整套文档的组织方式。
- [教程](docs/tutorials/index.zh.md)：从这里开始 —— 快速 CLI 演示、第一个 harness 应用、添加 skill 与 MCP。
- [操作指南](docs/how-to/index.zh.md)：以任务为中心的食谱，涵盖模型配置、插件安装、运行与部署。
- [参考](docs/reference/index.zh.md)：环境变量、CLI 命令、包、文件布局、模板、Docker。
- [概念解释](docs/explanation/index.zh.md)：agentseek 是什么、它与 Bub 的关系、运行时数据模型、扩展模型。
- [博客入口](docs/blog/index.zh.md)：发布说明、迁移信息和更长篇的文章入口。
- [认识 agentseek](docs/blog/introducing-agentseek.zh.md)：介绍从 bubseek 到 agentseek 的演进、数据库原生 harness 的定位，以及 Bub/tape store。

各个 contrib package 的完整安装与使用方式仍然写在各自的 README 里：

- [agentseek-observability](contrib/agentseek-observability/README.md)
- [agentseek-tapestore-oceanbase](contrib/agentseek-tapestore-oceanbase/README.md)
- [agentseek-langchain](contrib/agentseek-langchain/README.md)
- [agentseek-schedule-sqlalchemy](contrib/agentseek-schedule-sqlalchemy/README.md)

## 工作原理

- **两个包、两条路径** —— `agentseek-cli`（项目生命周期 CLI）与 `agentseek`（harness）。命令名相同，命令面不同。详见 [`docs/explanation/choosing-an-entry-point.zh.md`](docs/explanation/choosing-an-entry-point.zh.md)。
- **Bub 作为上游 runtime** —— [Bub](https://github.com/bubbuild/bub) 提供 hook-first turn pipeline、tape store、skills、plugins 和 channel model；harness 在它上面运行。agentseek 把 Bub 作为库消费，不是对它重新包装。
- **`.agentseek` 运行时 home** —— harness 启动时把当前工作区下的 `.agentseek/` 作为运行时 home；`agentseek install` 使用 `agentseek-project` 作为默认插件沙箱。可通过 [`docs/reference/environment.zh.md`](docs/reference/environment.zh.md) 中的环境变量覆盖。
- **环境变量别名** —— `AGENTSEEK_*` 会为同名 `BUB_*` 提供回退值，因此项目可以使用自己的命名空间，同时保持与上游兼容。
- **开放式 authoring model** —— `AGENTS.md`、项目级本地 skills、内置 skills 和 MCP 配置，都是一等公民的编写与扩展入口。
- **Contrib 扩展路径** —— 数据库存储、LangChain 路由、持久化调度以及其他更大的集成，都放在 `contrib/` 下，并在各自目录维护完整用法文档。

如果你想从本地开发一路平滑走到更大的部署场景，我们推荐 [OceanBase seekdb](https://github.com/oceanbase/seekdb) 和 OceanBase。

## 开发

```bash
make install
make check
make test
make docs-test
```

各个 contrib package 的 README 里记录了它们各自的检查命令。

## License

[Apache-2.0](LICENSE)
