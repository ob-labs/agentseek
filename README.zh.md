# agentseek

中文 | [English](README.md)

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

一个由 [OceanBase](https://www.oceanbase.com/) OSS Team 提供的数据库原生 Agent Harness。

## agentseek 是什么

agentseek 是一个面向团队的数据库原生 Agent Harness，适合那些希望把 agent 运行时数据变成一等数据库工作负载的场景。

它把数据库视为承载 agent 上下文、执行历史、工具调用、任务、反馈和观测数据的自然位置。这样，同一份运行时数据就可以直接服务于调试、回放、轨迹对比、评估、分析和训练工作流，而不需要复制到多个系统中，也不需要事后重新导入。

agentseek 在 [Bub](https://github.com/bubbuild/bub) 之上提供 agentseek 的默认配置、环境变量别名和项目级运行时布局。当你希望继续使用 Bub 的运行时模型，但把项目本地 `.agentseek` 目录和 `AGENTSEEK_*` 配置作为默认入口时，就使用 `agentseek`。

## 为什么存在

大多数 agent 的价值都体现在运行时，但它们的运行时数据往往散落在 JSONL 日志、Markdown 笔记、SQLite 文件、tracing 系统、对象存储和离线流水线之间。第一次交互之后，这些数据再想查询、回放、比较、评估或转成训练材料，成本就会迅速上升。

agentseek 从另一个前提出发：上下文、记忆、任务、工具调用、trace、反馈和评估材料，从一开始就应该共享同一个持久化底座。对 agent 系统来说，这让运行时数据具备复用价值；对数据库来说，这意味着它不再只存放最终业务结果，而是可以直接承载智能应用的工作负载。

## 快速开始

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

配置一个模型，然后启动本地 chat：

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
uv run agentseek chat
```

`agentseek` 是一个兼容 Bub 的发行版入口。默认情况下，它会把当前工作区下的 `.agentseek` 作为本地配置目录和运行时 home。若你需要上游 Bub CLI 或直接使用 Bub 插件，也可以直接执行 `uv run bub ...`。

项目级本地 skills 放在 `.agents/skills` 下即可在本地运行中生效，因为 Bub 会从工作区自动发现项目 skills。对于 MCP，`bub-mcp` 默认使用 `${BUB_HOME}/mcp.json`，在 agentseek 默认布局下会对应到 `.agentseek/mcp.json`；如果你更希望把它放在项目根目录的 `.agents/mcp.json`，则设置 `AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json`。

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
- [Blog intro](docs/blog/index.zh.md)：发布说明、迁移信息和更长篇的文章入口。
- [Introducing agentseek](docs/blog/introducing-agentseek.zh.md)：介绍从 bubseek 到 agentseek 的演进、数据库原生 harness 的定位，以及 Bub/tape 上下文。
- [Getting started](docs/docs/getting-started.zh.md)：本地运行 agentseek 或通过 Docker Compose 启动的教程。
- [Configuration](docs/docs/configuration.zh.md)：agentseek 环境变量别名、本地运行时路径和 Docker 默认值的参考文档。
- [Extensions](docs/docs/extensions.zh.md)：如何增加项目指令、skills、MCP 配置和 Bub 兼容插件。

各个 contrib package 的完整安装与使用方式仍然写在各自的 README 里：

- [agentseek-observability](contrib/agentseek-observability/README.md)
- [agentseek-tapestore-oceanbase](contrib/agentseek-tapestore-oceanbase/README.md)
- [agentseek-langchain](contrib/agentseek-langchain/README.md)
- [agentseek-schedule-sqlalchemy](contrib/agentseek-schedule-sqlalchemy/README.md)

## 工作原理

- **Bub 作为运行时层**： [Bub](https://github.com/bubbuild/bub) 提供 CLI、hook-first turn pipeline、tape context、skills、plugins 和 channel model。agentseek 以 Bub 作为默认治理层，而不是把产品边界停在 Bub 本身。
- **项目级本地默认值**：`.agentseek` 是默认运行时 home，`agentseek-project` 是 `agentseek install` 使用的默认插件沙箱。
- **环境变量别名**：`AGENTSEEK_*` 会为同名 `BUB_*` 提供回退值，因此 agentseek 项目可以使用自己的命名空间，同时保持与 Bub 兼容。
- **开放式 authoring model**：`AGENTS.md`、项目级本地 skills、内置 skills 和 MCP 配置，都是一等公民的编写与扩展入口。
- **Contrib 扩展路径**：数据库存储、LangChain 路由、持久化调度以及其他更大的集成，都放在 `contrib/` 下，并在各自目录维护完整用法文档。

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
