# AgentSeek

中文 | [English](README.md)

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

AgentSeek 是面向本地 AI 生态应用开发的 template-first toolkit。它帮助开发者
创建应用、运行应用、查看本地生命周期状态，并诊断常见环境问题，然后再逐步进入
[OceanBase](https://www.oceanbase.com/) AI 生态。

> **《Deep Agents 实战》**：基于 AgentSeek 实验的 LangChain / DeepAgents 免费课程。
> [课程仓库](https://github.com/datawhalechina/deepagents-in-action/)

## 从这里开始

日常使用时先安装 CLI：

```bash
uv tool install agentseek
```

如果只是临时试用，也可以把第一条 `agentseek create ...` 命令替换为
`uvx agentseek create ...`。

创建一个可以继续编辑的项目：

```bash
agentseek create bub/default --no-input
cd my_bub_agent
cp .env.example .env
uv sync
npm install --prefix frontend
```

在 `.env` 中设置 `BUB_MODEL` 和对应 provider key，然后使用外部生命周期命令：

```bash
agentseek doctor
agentseek dev
agentseek info
agentseek task --list
```

## 生命周期命令

| 命令 | 用途 |
| --- | --- |
| `create` | 渲染应用模板。 |
| `doctor` | 检查本地项目就绪状态。 |
| `dev` | 启动本地开发栈。 |
| `info` | 输出项目入口和 lifecycle 元数据。 |
| `task` | 运行项目定义的任务。 |

## 文档

- [文档首页](docs/index.md)
- [快速开始](docs/get-started/index.md)
- [指南](docs/guides/index.md)
- [参考](docs/reference/index.md)
- [概念](docs/concepts/index.md)

## 相关项目

- [Bub](https://github.com/bubbuild/bub)：默认生成项目使用的 hook-first agent runtime。
- [ContextSeek](https://github.com/ob-labs/contextseek)：语义记忆、检索和 MCP 集成。
- [agentseek-api](https://github.com/ob-labs/agentseek-api)：面向生产 LangGraph 服务的 Agent Protocol server。
- [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase)：OceanBase 上的 LangGraph checkpoint、store、向量检索和混合检索。

## 开发

贡献者从本地源码副本开始：

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
make install
make check
make test
make docs-test
```

## License

[Apache-2.0](LICENSE)
