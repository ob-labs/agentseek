# AgentSeek

[中文](README.zh.md) | English

[![License](https://img.shields.io/github/license/ob-labs/agentseek.svg)](LICENSE)
[![CI](https://github.com/ob-labs/agentseek/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain)

A database-native Agent Harness, by the [OceanBase](https://en.oceanbase.com/) OSS Team.

## What AgentSeek is

AgentSeek is a database-native Agent Harness for teams that want agent runtime data to become a first-class database workload. It is open to any Agent Framework — the current version ships with built-in Bub and is LangChain-friendly out of the box.

It treats the database as the natural place to keep agent context, execution history, tool calls, tasks, feedback, and observability together. The same runtime data can then serve debugging, replay, trajectory comparison, evaluation, analysis, and training workflows without being copied into separate systems or re-ingested later.

**AgentSeek is a suite** of components that work independently or together:

| Component | What it does | Repo |
| --- | --- | --- |
| **agentseek-cli** | Scaffold projects, manage lifecycle (`create / run / build / deploy`) | [ob-labs/agentseek](https://github.com/ob-labs/agentseek) |
| **agentseek-api** | Agent Protocol server — ship your LangGraph to production, zero code change | [ob-labs/agentseek-api](https://github.com/ob-labs/agentseek-api) |
| **ContextSeek** | Semantic context layer — memory, retrieval, evolution, progressive disclosure. Ships with LangChain middleware and LangSmith `@traceable` support | [ob-labs/contextseek](https://github.com/ob-labs/contextseek) |
| **langchain-oceanbase** | Data substrate — checkpoint + store + vector + hybrid search on OceanBase / seekdb / MySQL | [oceanbase/langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) |

Each component has its own repo and docs. This repo documents the suite-level workflow; for component-specific API details, follow the links above.

## Quick Start — for LangChain developers

**Which template should I pick?**

- **Starting fresh / learning?** → `langchain/markdown-messages` (minimal, 5 min)
- **Already have a graph, need to deliver a product?** → `langchain/default` (frontend + Feishu IM + full runtime)
- **Need deep research with sub-agents?** → `deepagents/research` (Tavily + report generation)
- **Graph runs on a remote server?** → `langchain/cli-remote`

```bash
# Pick one and run:
uvx --from agentseek-cli agentseek create langchain --template markdown-messages
# or: langchain --template default
# or: deepagents --template research
```

Then: `cd <project> && uv sync && uv run langgraph dev` (minimal) or `uv run agentseek run` (full delivery).

> **LangSmith tracing is pre-configured.** Every template ships a `.env.example` with `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` ready to fill in.

**Next steps after your agent runs:**

- Add persistent memory → [ContextSeek docs](https://github.com/ob-labs/contextseek)
- Ship to production as a service → [agentseek-api docs](https://github.com/ob-labs/agentseek-api)
- Switch to a durable database → [langchain-oceanbase docs](https://github.com/oceanbase/langchain-oceanbase)
- Install dev skills for guided help → see [Development skills](#development-skills) below
- Study DeepAgents systematically → see [Open-source course](#open-source-course) below

### For OceanBase / seekdb / MySQL developers

Already running OceanBase, seekdb, or MySQL? AgentSeek uses your database as the data substrate for AI agents.

```bash
pip install langchain-oceanbase[pyseekdb]   # OceanBase / seekdb
pip install langchain-oceanbase             # MySQL (checkpoint + store)
```

MySQL users get checkpoint and store out of the box; vector search requires OceanBase or seekdb. Full docs: [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase).

### Other paths

AgentSeek ships as two complementary PyPI packages split by job:

- **`agentseek-cli`** — the **project lifecycle CLI** (`create`, `run`, `build`, `deploy`, `api`, `ctx`, `skills`). Self-contained, installable with `uv tool install agentseek-cli`.
- **`agentseek`** — the **harness** itself. Provides the runtime CLI (`chat`, `run`, `gateway`, `install`, `update`, …) and the library you embed in your application. Resolved through this repository's `[tool.uv.sources]`.

**Already using [Bub](https://github.com/bubbuild/bub)?** AgentSeek is a distribution of Bub with opinionated defaults. Try `agentseek create bub --template default`. See [How AgentSeek relates to Bub](docs/explanation/bub-relationship.md).

See [Choosing an entry point](docs/explanation/choosing-an-entry-point.md) for the full comparison.

## Open-source course

**"Deep Agents 实战"** — a free course on building production-grade AI agents with LangChain / DeepAgents. All hands-on labs use AgentSeek.

[Course site](https://webup.github.io/deepagents-course) · [Source repo](https://github.com/webup/deepagents-site)

Topics covered: Agent Harness concepts, virtual filesystem, task planning, sub-agents, async delegation, long-term memory, Human-in-the-Loop, skills, sandboxes, streaming frontends, and production deployment.

## Development skills

Installable guides that live inside your AI coding agent (Claude Code, Cursor, etc.):

| Skill | What it does |
| --- | --- |
| **langchain-dev-guide** | LangChain / LangGraph engineering pitfalls and verified fixes. Covers DeepAgents, middleware, streaming, multi-agent orchestration. |
| **langchain-cn-models** | Step-by-step recipes for integrating Chinese LLM providers (DeepSeek, Qwen, GLM, Moonshot) into LangChain. |

```bash
npx skills add ob-labs/agentseek --all
```

Full details: [skills/](skills/)

## Connect your Agent Framework

AgentSeek is designed to be the harness underneath any Agent Framework. If you build on LlamaIndex, AutoGen, CrewAI, or your own orchestration — we welcome you to connect it. AgentSeek brings the data substrate (OceanBase / seekdb / MySQL), the semantic context layer (ContextSeek), and production serving (agentseek-api) so you don't have to build those yourself.

The integration pattern follows `agentseek-langchain` — a contrib plugin that bridges your runnable into the harness. See [Extension model](docs/explanation/extension-model.md) and [Author a contrib plugin](docs/how-to/author-a-contrib-plugin.md). PRs to `contrib/` welcome.

## Templates

Templates are a **growing collection** — we are continuously adding new ones and polishing existing ones for both the LangChain and Bub families. PRs welcome.

| Template | Description |
| --- | --- |
| `langchain/markdown-messages` | Pure LangChain chatbot, `langgraph dev` backend, markdown-rendered frontend. |
| `langchain/default` | LangChain + CopilotKit frontend + Feishu IM gateway + full agentseek runtime. |
| `langchain/cli-remote` | Remote LangGraph server bridged via `LangGraphClientRunnable`. |
| `deepagents/research` | DeepAgents research agent with Tavily search and streamed report UI. |
| `deepagents/default` | `create_deep_agent` bound to `agentseek-langchain`. |
| `bub/default` | Lightweight Bub agent with CopilotKit frontend, no LangChain. |

See [Templates reference](docs/reference/templates.md) for inputs, generated layout, and next steps.

## Docker Compose

```bash
cp .env.example .env
make compose-up
```

See [How to run with Docker Compose](docs/how-to/run-with-docker-compose.md).

## Documentation

- [Home](docs/index.md) — suite overview, multi-persona quick starts
- [Tutorials](docs/tutorials/index.md) — quick demo, first app, skills and MCP
- [How-to guides](docs/how-to/index.md) — task-focused recipes
- [Explanation](docs/explanation/index.md) — LangChain relationship, Bub relationship, runtime data model
- [Reference](docs/reference/index.md) — env vars, CLI, packages, templates, Docker

Contrib packages document their setup in their own READMEs:

- [agentseek-langchain](contrib/agentseek-langchain/README.md)
- [agentseek-tapestore-oceanbase](contrib/agentseek-tapestore-oceanbase/README.md)
- [agentseek-observability](contrib/agentseek-observability/README.md)
- [agentseek-contextseek](contrib/agentseek-contextseek/README.md)
- [agentseek-schedule-sqlalchemy](contrib/agentseek-schedule-sqlalchemy/README.md)

## How it works

- **Suite of components** — agentseek-cli, agentseek-api, ContextSeek, langchain-oceanbase. Use together or independently.
- **Bub as the runtime kernel** — [Bub](https://github.com/bubbuild/bub) provides the hook-first turn pipeline, tape store, skills, plugins, and channel model. AgentSeek consumes Bub as a library dependency.
- **LangChain bridge** — the `agentseek-langchain` contrib plugin connects LangGraph runnables into the harness turn pipeline transparently.
- **`.agentseek` runtime home** — workspace-local config, plugin sandbox, and runtime state.
- **Environment aliases** — `AGENTSEEK_*` values act as fallbacks for matching `BUB_*` values.
- **Open authoring model** — `AGENTS.md`, project-local skills, and MCP config are first-class extension points.

For a good default experience from local development to larger deployments, we recommend [OceanBase seekdb](https://github.com/oceanbase/seekdb) and OceanBase.

## Development

```bash
make install
make check
make test
make docs-test
```

## License

[Apache-2.0](LICENSE)
