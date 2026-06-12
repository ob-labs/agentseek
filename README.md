# AgentSeek

[中文](README.zh.md) | English

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

AgentSeek is a database-native agent harness by the
[OceanBase](https://en.oceanbase.com/) OSS Team.

It helps you move from a local agent turn to an editable application project,
then to runtime extensions and deployment manifests when the project is ready.

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
uvx agentseek create bub/default --no-input
cd my_bub_agent
cp .env.example .env
uv sync
npm install --prefix frontend
```

Set `AGENTSEEK_API_KEY` in `.env`, then start the app:

```bash
uv run agentseek run --no-browser
```

If you are extending AgentSeek inside an existing Python project, add it as a
dependency:

```bash
uv add agentseek
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

Contributors work from a repository checkout:

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
