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

## Quick Start

| Goal | Commands | Use it when |
| --- | --- | --- |
| Manage projects | `agentseek create/run/build/deploy` | You want to scaffold, run, package, or deploy an application. |
| Run the harness | `agentseek chat/turn/gateway` | You want to evaluate, embed, or operate the runtime. |
| Extend the runtime | `agentseek plugin/ctx/skills/api` | You want plugins, context, skills, or service bridges. |

### Create a template project

```bash
uv tool install agentseek
agentseek create --list-templates
agentseek create langchain/markdown-messages
cd markdown_messages_agent
cp .env.example .env
uv sync
uv run langgraph dev
```

Use this path when you want a generated application scaffold. Templates cover
LangChain, DeepAgents, and lightweight starters.

### Run the harness

```bash
agentseek chat
```

Use this path when you want the harness runtime directly: a chat loop, gateway,
plugins, MCP, or an embeddable Python package.

For all commands and options, see the [CLI reference](docs/reference/cli.md).

## Repository Overview

| Component | Role |
| --- | --- |
| `agentseek` | CLI, harness runtime, project commands, and embeddable library. |
| `templates/` | Cookiecutter starters for common application shapes. |
| `contrib/` | Optional integrations for frameworks, storage, and context systems. |

Related projects:

| Project | Role |
| --- | --- |
| [agentseek-api](https://github.com/ob-labs/agentseek-api) | Agent Protocol server for production LangGraph serving. |
| [ContextSeek](https://github.com/ob-labs/contextseek) | Semantic memory, retrieval, evolution, HTTP API, MCP, and LangChain middleware. |
| [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) | LangGraph checkpoint, store, vector search, and hybrid search on OceanBase, seekdb, or MySQL. |

AgentSeek also builds on [Bub](https://github.com/bubbuild/bub), a hook-first
agent runtime and framework.

## Typical Workflow

The usual flow is:

1. Create a project when you need an application scaffold.
2. Run AgentSeek itself when you need the harness runtime.
3. Add durable runtime data through the harness and storage integrations.
4. Add semantic memory with ContextSeek when the agent needs cross-session context.
5. Serve production LangGraph apps through agentseek-api.

Storage, memory, and serving are added only when the application needs them.

## Template Choices

Pick the smallest template that matches your application:

| Application shape | Start with |
| --- | --- |
| Minimal LangChain app | `agentseek create langchain/markdown-messages` |
| Full AgentSeek delivery app | `agentseek create langchain/default` |
| DeepAgents research app | `agentseek create deepagents/research` |
| Lightweight app without LangChain | `agentseek create bub/default` |

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
