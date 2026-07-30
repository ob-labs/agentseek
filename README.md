# AgentSeek

[中文](README.zh.md) | English

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

AgentSeek is a template-first toolkit for local agent application development.
It gives editable generated projects one predictable lifecycle: discover,
create, inspect, configure, check, run, observe, and iterate.

AgentSeek 0.1.1 resolves lifecycle-v2 templates from the immutable
[`agentseek-ai/agentseek-templates` catalog](https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0).
The CLI lists templates from its embedded registry snapshot and fetches named
template content at the exact locked commit.

## Experience the local ADLC

Start with the shipped `deepagents/research` walkthrough. It creates a fully
editable DeepAgents research app with a native LangGraph backend and a React frontend
as its primary user experience.

```bash
# Install the lifecycle CLI, then create and enter the generated project.
uv tool install agentseek
agentseek create deepagents/research --no-input
cd research_deepagent

# Inspect declared entry points before configuring local credentials.
agentseek info
cp .env.example .env
cp frontend/.env.example frontend/.env
$EDITOR .env

# Run the setup tasks declared by this project, then check readiness.
agentseek task --list
agentseek task sync
agentseek task frontend
agentseek doctor

# Preview the native commands, run the local stack, and check live services.
agentseek dev --dry-run
agentseek dev
# In another terminal, after agentseek dev starts, check live services.
agentseek doctor --live
```

The current scaffold declares only `sync` and `frontend` setup tasks. Its
native backend resolves to `uv run langgraph dev --port 2024 --no-browser`,
while the frontend resolves to `npm run dev` in `frontend/`.

For a one-off run, use `uvx agentseek create deepagents/research --no-input`
instead of installing the CLI.

## What is AgentSeek?

AgentSeek supplies the stable lifecycle surface around a generated project; it
does not own that project's source, framework, runtime, or deployment. A
template selects those pieces, and the generated project remains yours to edit.

![AgentSeek architecture](https://raw.githubusercontent.com/ob-labs/agentseek/v0.1.1/diagram/agentseek-readme/agentseek-architecture-en.svg)

The CLI connects people, coding agents, and desktop clients to a locked,
versioned template catalog and an editable project lifecycle contract. The
project then owns its runtimes and integrations, including models, tools, MCP
servers, and external services.

## Agent Development Lifecycle

The local ADLC keeps iteration anchored in the existing project instead of
starting over: discover, create, inspect, configure, check, run, observe, and
iterate back to inspect.

![Agent development lifecycle](https://raw.githubusercontent.com/ob-labs/agentseek/v0.1.1/diagram/agentseek-readme/agentseek-adlc-en.svg)

| Stage | Local command or project surface |
| --- | --- |
| Discover | `agentseek create --list-templates` finds templates by goal. |
| Create | `agentseek create` renders an editable project. |
| Inspect | `agentseek info` shows its declared entry points and topology. |
| Configure | `.env` and project configuration provide runtime credentials and choices. |
| Check | `agentseek doctor` validates local readiness. |
| Run | `agentseek dev` starts the template-owned local stack. |
| Observe | `agentseek doctor --live` and lifecycle signals show its current state. |
| Iterate | Change the generated project, then return to **Inspect**. |

## Observability throughout the loop

Lifecycle diagnostics answer whether the declared project is ready and running:
`agentseek info` shows topology, `agentseek doctor` performs preflight checks,
and `agentseek doctor --live` checks declared services after startup. For
Desktop, scripts, and other machine consumers, use the versioned JSON contract
instead of parsing human output.

```bash
agentseek info --json
agentseek doctor --json
agentseek doctor --live --json
AGENTSEEK_CONSOLE=true agentseek doctor --live
```

`info --json` contains normalized services, references, and safe actions such
as which URL can be opened directly. It never includes environment values or
raw process or task commands. `AGENTSEEK_CONSOLE=true` enables local CLI spans
and lifecycle events. Optional LangSmith tracing, configured through the
settings already present in `deepagents/research`, answers what the agent did
inside an individual run.

## Guided templates

Choose by goal, then inspect a specific template before creating it. AgentSeek
maintains many templates without requiring you to memorize a catalog dump.

```bash
agentseek create --list-templates
agentseek create --list-templates --filter deepagents
agentseek create deepagents/research --describe
```

## Core concepts and commands

| Concept | What it provides |
| --- | --- |
| Template | A complete, editable application scaffold with its chosen runtime. |
| Lifecycle file | The project-owned declaration of paths, environment checks, services, processes, and tasks. |
| AgentSeek CLI | A consistent local interface for the declared lifecycle. |

| Command | Purpose |
| --- | --- |
| `create` | Render an application template. |
| `info` | Show declared entry points and lifecycle metadata. |
| `task` | Run a project-defined setup task. |
| `doctor` | Check local readiness or live declared-service health. |
| `dev` | Run the local development stack. |

## Documentation

- [Documentation home](https://ob-labs.github.io/agentseek/)
- [Get started](https://ob-labs.github.io/agentseek/get-started/)
- [Guides](https://ob-labs.github.io/agentseek/guides/)
- [Reference](https://ob-labs.github.io/agentseek/reference/)
- [Concepts](https://ob-labs.github.io/agentseek/concepts/)

## Development

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
make install
make check
make test
make docs-test
```

## Community and course

Explore **Deep Agents in Action**, a free LangChain / DeepAgents course with
AgentSeek labs, in the [course repository](https://github.com/datawhalechina/deepagents-in-action/).
Join or follow project discussion through [GitHub Discussions](https://github.com/ob-labs/agentseek/discussions).

## License

[Apache-2.0](LICENSE)
