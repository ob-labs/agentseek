---
hide_sidebar: true
---

# AgentSeek Documentation

AgentSeek is a database-native Agent Harness for building agent applications
whose runtime data is durable, queryable, and ready to operate.

Use these docs to answer three questions:

1. Where should I start?
2. Which guide covers the task in front of me?
3. Where do I find reference details after the first run works?

## Fast Paths

| Goal | Start here |
| --- | --- |
| Create a template project | [Build your first harness app](tutorials/02-first-harness-app.md) |
| Run AgentSeek itself | [Quick demo via the CLI](tutorials/01-quick-demo-cli.md) |
| Configure model credentials | [Configure model providers](how-to/configure-model.md) |
| Run a generated project locally | [Run locally](how-to/run-locally.md) |
| Build and deploy a generated project | [Build and deploy](how-to/build-and-deploy.md) |

## Start With One Flow

| Flow | Start here | Use it when |
| --- | --- |
| Create a project from templates | [Build your first harness app](tutorials/02-first-harness-app.md) | You want a working application scaffold. |
| Run AgentSeek itself | [Quick demo via the CLI](tutorials/01-quick-demo-cli.md) | You want to evaluate or operate the harness runtime. |

After the first run works, continue with the guide that matches the next job:

| Need | Start here |
| --- | --- |
| A minimal [LangChain](https://github.com/langchain-ai/langchain) app | `langchain/markdown-messages` in [Templates reference](reference/templates.md). |
| A full product-shaped generated app | `langchain/default`, then [Run locally](how-to/run-locally.md) and [Build and deploy](how-to/build-and-deploy.md). |
| A [DeepAgents](https://docs.langchain.com/oss/deepagents) project | Compare `deepagents/research`, `deepagents/content-builder`, and `langchain/sandbox` in [Templates reference](reference/templates.md). |
| A lightweight app without LangChain | Start with the `bub/default` template. |
| Adding persistent memory | Use [agentseek-contextseek](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-contextseek) or the [ContextSeek](https://github.com/ob-labs/contextseek) project. |
| Choosing a database backend | Read [langchain-oceanbase](https://github.com/oceanbase/langchain-oceanbase) and [runtime data model](explanation/runtime-data-model.md). |

## Reference Details

| Need | Reference |
| --- | --- |
| How commands are organized | [Command overview](explanation/cli-surface.md) |
| Every command and flag | [CLI reference](reference/cli.md) |
| Every template | [Templates reference](reference/templates.md) |
| Package and repository boundaries | [Packages reference](reference/packages.md) |

## Common Commands

```bash
# Browse templates
uvx agentseek create --list-templates

# Create a minimal LangChain project
uvx agentseek create langchain/markdown-messages

# Run AgentSeek itself
uv tool install agentseek
agentseek chat
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
