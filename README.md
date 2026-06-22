# AgentSeek

[中文](README.zh.md) | English

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

AgentSeek is a template-first toolkit for developing AI ecosystem apps locally.
It helps developers create an app, run it, inspect its local lifecycle, and
diagnose common setup issues before moving deeper into the
[OceanBase](https://en.oceanbase.com/) AI ecosystem.

> **"Deep Agents in Action"**: a free LangChain / DeepAgents course with AgentSeek labs.
> [Course repo](https://github.com/datawhalechina/deepagents-in-action/)

## Start Here

Create a project you can edit:

```bash
uvx agentseek create bub/default --no-input
cd my_bub_agent
cp .env.example .env
uv sync
npm install --prefix frontend
```

Set `BUB_MODEL` and a matching Bub provider key in `.env`, then use the
external lifecycle commands:

```bash
uvx agentseek doctor
uvx agentseek dev
uvx agentseek info
uvx agentseek task --list
```

## Documentation

The documentation is temporarily reduced to a single placeholder while the
project is being redesigned: [docs/index.md](docs/index.md).

## Related Projects

- [Bub](https://github.com/bubbuild/bub): hook-first agent runtime used by the default generated project.
- [ContextSeek](https://github.com/ob-labs/contextseek): semantic memory, retrieval, and MCP integration.
- [agentseek-api](https://github.com/ob-labs/agentseek-api): Agent Protocol server for production LangGraph serving.
- [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase): OceanBase-backed LangGraph checkpointing, store, vector search, and hybrid search.

## Development

Contributors work from a local source copy:

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
