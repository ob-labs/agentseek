# AgentSeek

中文 | [English](README.md)

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

AgentSeek 是由 [OceanBase](https://www.oceanbase.com/) OSS Team 提供的
数据库原生 agent harness。

它帮助你从一次本地 agent turn 开始，进入一个可编辑的应用项目；项目成熟后，
再加入 runtime 扩展和部署 manifests。

## 从这里开始

用 `uvx` 跑通最短路径：

```bash
mkdir agentseek-demo
cd agentseek-demo
AGENTSEEK_MODEL=openrouter:moonshotai/kimi-k2:free \
AGENTSEEK_API_KEY=sk-or-v1-replace-me \
uvx agentseek chat
```

创建一个可以继续编辑的项目：

```bash
uvx agentseek create bub/default --no-input
cd my_bub_agent
cp .env.example .env
uv sync
npm install --prefix frontend
```

在 `.env` 中设置 `AGENTSEEK_API_KEY`，然后启动应用：

```bash
uv run agentseek run --no-browser
```

## 文档

- [首页](docs/index.zh.md)：从文档中选择最短路径。
- [教程](docs/tutorials/index.zh.md)：跟随引导完成首次运行。
- [第一个 harness 应用](docs/tutorials/02-first-harness-app.zh.md)：创建并运行可编辑项目。
- [操作指南](docs/how-to/index.zh.md)：首次跑通后的任务食谱。
- [参考](docs/reference/index.zh.md)：命令、环境变量、包和模板。
- [Hub](docs/hub.zh.md)：bundled 与 contrib integrations。

## 相关项目

- [Bub](https://github.com/bubbuild/bub)：AgentSeek 底层使用的 hook-first agent runtime。
- [ContextSeek](https://github.com/ob-labs/contextseek)：语义记忆、检索和 MCP 集成。
- [agentseek-api](https://github.com/ob-labs/agentseek-api)：面向生产 LangGraph 服务的 Agent Protocol server。
- [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase)：OceanBase 上的 LangGraph checkpoint、store、向量检索和混合检索。

## 开发

贡献者从仓库 checkout 开始：

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
