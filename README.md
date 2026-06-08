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

> **"Deep Agents 实战"**: a free LangChain / DeepAgents course with AgentSeek labs.
> [Course site](https://webup.github.io/deepagents-course) · [Source repo](https://github.com/webup/deepagents-course)

## Two Entry Points

The two entry points serve different jobs:

| Goal | Start here | Use it when |
| --- | --- | --- |
| Create a project from templates | `agentseek new` | You want a working application scaffold. |
| Run AgentSeek itself | `agentseek chat` or `agentseek gateway` | You want to evaluate, embed, or operate the harness runtime. |

### Create a template project

```bash
uvx --from agentseek-cli agentseek new --list-templates
uvx --from agentseek-cli agentseek new langchain/markdown-messages
cd markdown_messages_agent
cp .env.example .env
uv sync
uv run langgraph dev
```

Use this path when you want a generated application shape first. Templates cover
LangChain, DeepAgents, and Bub starters.

### Run AgentSeek itself

```bash
uv tool install agentseek
agentseek chat
```

Use this path when you want the harness runtime directly: a chat loop, gateway,
plugins, MCP, or an embeddable Python package.

For install choices and command ownership, see
[Choosing an entry point](docs/explanation/choosing-an-entry-point.md).

## What Is In This Repository

This repository contains the pieces needed to create projects and run the
AgentSeek harness.

| Piece | Role |
| --- | --- |
| `agentseek` | Harness runtime and embeddable library. |
| `agentseek-cli` | Project creation and lifecycle commands. |
| Templates | Cookiecutter starters for common application shapes. |
| `contrib/` | Optional integrations for frameworks, storage, and context systems. |

Related projects live in their own repositories:

| Project | Role |
| --- | --- |
| [agentseek-api](https://github.com/ob-labs/agentseek-api) | Agent Protocol server for production LangGraph serving. |
| [ContextSeek](https://github.com/ob-labs/contextseek) | Semantic memory, retrieval, evolution, HTTP API, MCP, and LangChain middleware. |
| [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) | LangGraph checkpoint, store, vector search, and hybrid search on OceanBase, seekdb, or MySQL. |

AgentSeek also builds on [Bub](https://github.com/bubbuild/bub), a hook-first
agent runtime and framework.

## How The Pieces Fit

The usual flow is:

1. Create a project when you need an application scaffold.
2. Run AgentSeek itself when you need the harness runtime.
3. Add durable runtime data through the harness and storage integrations.
4. Add semantic memory with ContextSeek when the agent needs cross-session context.
5. Serve production LangGraph apps through agentseek-api.

This keeps the entry points simple while leaving room to add storage, memory,
and serving only when the application needs them.

## Template Choices

After you choose the template creation entry point, pick the smallest template
that matches the application shape:

| Application shape | Start with |
| --- | --- |
| Minimal LangChain app | `agentseek new langchain/markdown-messages` |
| Full AgentSeek delivery app | `agentseek new langchain/default` |
| DeepAgents research app | `agentseek new deepagents/research` |
| Bub app without LangChain | `agentseek new bub/default` |

See [Templates reference](docs/reference/templates.md) for the full catalogue.

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
