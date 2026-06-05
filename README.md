# AgentSeek

[中文](README.zh.md) | English

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

A database-native Agent Harness by the [OceanBase](https://en.oceanbase.com/) OSS Team.

AgentSeek helps teams turn agent runtime data into a database workload: turns,
context, tool calls, tasks, feedback, checkpoints, memory, and observability
stay queryable instead of being scattered across logs and side systems.

It is built for teams that want to move from a local
[LangChain](https://github.com/langchain-ai/langchain),
[DeepAgents](https://docs.langchain.com/oss/deepagents), or
[Bub](https://github.com/bubbuild/bub) prototype to a maintainable agent
application with a clear runtime, storage, context, and serving story.

## Start Here

Create a project from a template:

```bash
uvx --from agentseek-cli agentseek create --template
uvx --from agentseek-cli agentseek create langchain/markdown-messages
cd markdown_messages_agent
cp .env.example .env
uv sync
uv run langgraph dev
```

For a full delivery path with the AgentSeek runtime, use a richer template:

```bash
uvx --from agentseek-cli agentseek create langchain/default
cd my_langchain_agent
cp .env.example .env
uv sync
uv run agentseek run
```

See [Templates reference](docs/reference/templates.md) for the full catalogue:
LangChain, DeepAgents, and Bub templates are all available through
`agentseek create --template`.

## What This Repo Owns

AgentSeek is a suite. This repository is the home for the harness distribution,
the lifecycle CLI, templates, docs, and contrib integrations.

| Piece | Role | When you use it |
| --- | --- | --- |
| `agentseek` | Harness runtime and library | You embed or run the turn pipeline, gateway, skills, plugins, and runtime state. |
| `agentseek-cli` | Project lifecycle CLI | You create, run, build, deploy, and inspect generated projects. |
| Templates | Cookiecutter project starters | You need a working LangChain, DeepAgents, or Bub project shape quickly. |
| `contrib/` | Integration packages | You bridge frameworks or storage backends into the harness. |

Related projects live in their own repositories:

| Project | Role |
| --- | --- |
| [agentseek-api](https://github.com/ob-labs/agentseek-api) | Agent Protocol server for production LangGraph serving. |
| [ContextSeek](https://github.com/ob-labs/contextseek) | Semantic memory, retrieval, evolution, HTTP API, MCP, and LangChain middleware. |
| [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) | LangGraph checkpoint, store, vector search, and hybrid search on OceanBase, seekdb, or MySQL. |

AgentSeek also builds on [Bub](https://github.com/bubbuild/bub), a hook-first
agent runtime and framework.

## How The Pieces Fit

The normal path is:

1. Use `agentseek-cli` to create a project from a template.
2. Run the generated project locally with `langgraph dev` or `agentseek run`.
3. Add durable runtime data through the harness and storage integrations.
4. Add semantic memory with ContextSeek when the agent needs cross-session context.
5. Serve production LangGraph apps through agentseek-api.

That split keeps the project boundaries clear: this repo gives you the harness,
CLI, templates, and integrations; the adjacent repos provide production serving,
semantic context, and database-specific LangChain storage.

## Choose A Path

| If you want to... | Start with |
| --- | --- |
| Build a minimal LangChain app | `agentseek create langchain/markdown-messages` |
| Build a full AgentSeek delivery app | `agentseek create langchain/default` |
| Build a DeepAgents research app | `agentseek create deepagents/research` |
| Use Bub without LangChain | `agentseek create bub/default` |
| Understand package boundaries | [Choosing an entry point](docs/explanation/choosing-an-entry-point.md) |
| Browse every CLI flag | [CLI reference](docs/reference/cli.md) |

## Documentation

- [Documentation home](docs/index.md)
- [Tutorials](docs/tutorials/index.md)
- [How-to guides](docs/how-to/index.md)
- [Explanation](docs/explanation/index.md)
- [Reference](docs/reference/index.md)

Useful package docs in this repo:

- [agentseek-langchain](contrib/agentseek-langchain/README.md)
- [agentseek-tapestore-oceanbase](contrib/agentseek-tapestore-oceanbase/README.md)
- [agentseek-contextseek](contrib/agentseek-contextseek/README.md)
- [agentseek-schedule-sqlalchemy](contrib/agentseek-schedule-sqlalchemy/README.md)

## Development

```bash
make install
make check
make test
make docs-test
```

## License

[Apache-2.0](LICENSE)
