# AgentSeek

[中文](README.zh.md) | English

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

AgentSeek is a database-native agent harness by the
[OceanBase](https://en.oceanbase.com/) OSS Team.

AgentSeek turns agent runtime data into a database workload: turns, context,
tool calls, tasks, feedback, checkpoints, memory, and observability data stay
queryable instead of being scattered across logs and side systems.

> **"Deep Agents in Action"**: a free LangChain / DeepAgents course with AgentSeek labs.
> [Course repo](https://github.com/datawhalechina/deepagents-in-action/)

## Start Here

Run the quickest local path with `uvx`:

```bash
mkdir agentseek-demo
cd agentseek-demo
AGENTSEEK_MODEL=openrouter:moonshotai/kimi-k2:free \
AGENTSEEK_API_KEY=sk-or-v1-replace-me \
uvx agentseek chat
```

Create a project you can edit:

```bash
uvx agentseek create deepagents/default --no-input
cd my_deepagent
cp .env.example .env
uv sync
uv pip install -r requirements.txt
```

Set `AGENTSEEK_API_KEY` in `.env`, then start the harness gateway:

```bash
export PYTHONPATH=src
export AGENTSEEK_LANGCHAIN_SPEC=my_deepagent.demo_binding:build_spec
export AGENTSEEK_AG_UI_PORT=18088
uv run agentseek gateway --enable-channel ag-ui
```

## Documentation

- [Home](docs/index.md): the shortest route through the docs.
- [Tutorials](docs/tutorials/index.md): guided first runs.
- [First harness app](docs/tutorials/02-first-harness-app.md): create and run an editable project.
- [How-to guides](docs/how-to/index.md): focused recipes after the first run.
- [Reference](docs/reference/index.md): commands, environment variables, packages, and templates.
- [Hub](docs/hub.md): bundled and contrib integrations.

## Related Projects

- [Bub](https://github.com/bubbuild/bub): hook-first agent runtime used underneath AgentSeek.
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
