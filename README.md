# AgentSeek

[中文](README.zh.md) | English

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

AgentSeek is an application development lifecycle toolkit for AI ecosystem apps.

It helps you create a working app, check local readiness, run the development
stack, and expose project tasks through one consistent command surface.

Each template can choose its own runtime and project layout. AgentSeek provides
the shared lifecycle workflow around those generated apps.

> **"Deep Agents in Action"**: a free LangChain / DeepAgents course with AgentSeek labs.
> [Course repo](https://github.com/datawhalechina/deepagents-in-action/)

## Quickstart

Install the CLI for daily use.

```bash
uv tool install agentseek
```

For a one-off run without installing the tool, replace the first
`agentseek create ...` command with `uvx agentseek create ...`.

```bash
agentseek create bub/default --no-input
cd my_bub_agent
cp .env.example .env
uv sync
npm install --prefix frontend
```

Set the model and provider credentials required by the selected template.
AgentSeek reads `.env` only for variables declared by the template lifecycle
spec; it does not inject `.env` into child processes.

```bash
agentseek doctor
agentseek dev
```

## Lifecycle Commands

| Command | Purpose |
| --- | --- |
| `create` | Render an app template. |
| `doctor` | Check local project readiness. |
| `dev` | Run the local development stack. |
| `info` | Print project entry points and lifecycle metadata. |
| `task` | Run project-defined tasks. |

## Core Concepts

- A template creates a complete editable app.
- A lifecycle file defines how the app is checked and run.
- AgentSeek gives those lifecycle tasks a stable command interface.

Template types currently include `bub`, `deepagents`, and `langchain`. Each
template can expose the same lifecycle commands with different runtimes.

## Documentation

- [Documentation home](docs/index.md)
- [Get started](docs/get-started/index.md)
- [Guides](docs/guides/index.md)
- [Reference](docs/reference/index.md)
- [Concepts](docs/concepts/index.md)

## Related Projects

- [Bub](https://github.com/bubbuild/bub): hook-first agent runtime used by one AgentSeek template path.
- [ContextSeek](https://github.com/ob-labs/contextseek): semantic memory, retrieval, and MCP integration.
- [agentseek-api](https://github.com/ob-labs/agentseek-api): Agent Protocol server for production LangGraph serving.
- [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase): OceanBase-backed LangGraph checkpointing, store, vector search, and hybrid search.

## Development

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
