---
hide_sidebar: true
---

# AgentSeek Documentation

AgentSeek is a database-native Agent Harness for building agent applications
whose runtime data is durable, queryable, and ready to operate.

Use these docs to answer three questions:

1. Should I create a template project or run AgentSeek itself?
2. Which package or adjacent project owns the capability I need?
3. How do I move from local development to memory, storage, gateway, and serving?

## Fast Paths

| Goal | Start here |
| --- | --- |
| Create a template project | [Build your first harness app](tutorials/02-first-harness-app.md) |
| Run AgentSeek itself | [Quick demo via the CLI](tutorials/01-quick-demo-cli.md) |
| Understand the two entry points | [Choosing an entry point](explanation/choosing-an-entry-point.md) |
| Configure model credentials | [Configure model providers](how-to/configure-model.md) |
| Run a generated project locally | [Run locally](how-to/run-locally.md) |
| Build and deploy a generated project | [Build and deploy](how-to/build-and-deploy.md) |

## Two Entry Points

| Job | Use | Start here |
| --- | --- |
| Create a project from templates | `agentseek-cli` and `agentseek create` | [Build your first harness app](tutorials/02-first-harness-app.md) and [Templates reference](reference/templates.md). |
| Run AgentSeek itself | `agentseek` harness runtime | [Quick demo via the CLI](tutorials/01-quick-demo-cli.md), then [Run locally](how-to/run-locally.md). |

After that, choose the specific application or operation you need:

| Need | Start here |
| --- | --- |
| A minimal [LangChain](https://github.com/langchain-ai/langchain) app | `langchain/markdown-messages` in [Templates reference](reference/templates.md). |
| A full product-shaped generated app | `langchain/default`, then [Run locally](how-to/run-locally.md) and [Build and deploy](how-to/build-and-deploy.md). |
| A [DeepAgents](https://docs.langchain.com/oss/deepagents) project | Compare `deepagents/research`, `deepagents/content-builder`, and `langchain/sandbox` in [Templates reference](reference/templates.md). |
| A [Bub](https://github.com/bubbuild/bub) app without LangChain | Start with `bub/default`, then read [How AgentSeek relates to Bub](explanation/bub-relationship.md). |
| Adding persistent memory | Use [agentseek-contextseek](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-contextseek) or the [ContextSeek](https://github.com/ob-labs/contextseek) project. |
| Choosing a database backend | Read [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) and [runtime data model](explanation/runtime-data-model.md). |

## Component Boundaries

AgentSeek is a suite, not a single monolith. The split matters when you are
choosing where to configure, extend, or debug something.

| Component | Boundary |
| --- | --- |
| `agentseek` | Runtime harness, gateway, skills/plugins, environment aliases, and local runtime state. |
| `agentseek-cli` | Project lifecycle commands: `create`, `run`, `build`, `deploy`, `api`, `ctx`, and `skills`. |
| Templates | Cookiecutter project starters under `templates/<framework>/<name>/`. |
| `contrib/` | Bridge packages such as `agentseek-langchain`, storage plugins, and ContextSeek integration. |
| agentseek-api | Separate production Agent Protocol server for LangGraph apps. |
| ContextSeek | Separate semantic context and memory system with HTTP, MCP, Python SDK, and LangChain middleware. |
| langchain-oceanbase | Separate LangChain storage integrations for OceanBase, seekdb, and MySQL. |

## Common Commands

```bash
# Browse templates
uvx --from agentseek-cli agentseek create --template

# Create a minimal LangChain project
uvx --from agentseek-cli agentseek create langchain/markdown-messages

# Run AgentSeek itself from this repository
uv run agentseek chat

# Run repository checks
make check
make test
make docs-test
```

## Documentation Map

<div class="terminal-grid terminal-grid-2">
  <div class="terminal-card">
    <h3><a href="tutorials/">Tutorials</a></h3>
    <p>Guided walkthroughs for the first app and common project setup.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="how-to/">How-to guides</a></h3>
    <p>Task-focused recipes for models, local runs, deployment, gateway, and ContextSeek.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="explanation/">Explanation</a></h3>
    <p>Design notes for package boundaries, Bub, LangChain, extensions, and runtime data.</p>
  </div>
  <div class="terminal-card">
    <h3><a href="reference/">Reference</a></h3>
    <p>Precise tables for CLI flags, templates, packages, environment variables, and file layout.</p>
  </div>
</div>
