---
title: Project lifecycle
type: explanation
audience: [A1, A2, A3, A4]
runs: no
verified_on: 2026-06-25
sources:
  - docs/tutorials/02-first-harness-app.md
  - docs/how-to/configure-model.md
  - docs/how-to/run-locally.md
  - docs/how-to/add-skills.md
  - docs/how-to/build-and-deploy.md
  - docs/reference/cli.md
---

# Project lifecycle

Use this page as a map for an AgentSeek project after the first CLI command.
Each stage links to the page that owns the detailed steps.

## Lifecycle map

| Stage | Goal | Detailed page |
| --- | --- | --- |
| Create | Generate an editable project from a maintained template. | [Build your first harness app](tutorials/02-first-harness-app.md) |
| Configure | Set model credentials, provider endpoints, and runtime environment. | [Configure model](how-to/configure-model.md), [Environment variables](reference/environment.md) |
| Run | Start a local app loop, chat path, gateway, or Compose stack. | [Run locally](how-to/run-locally.md), [Run the gateway](how-to/run-gateway.md), [Docker Compose](how-to/run-with-docker-compose.md) |
| Extend | Add skills, MCP tools, plugins, memory, or channel integrations. | [Add skills](how-to/add-skills.md), [Configure MCP](how-to/configure-mcp.md), [Install plugin](how-to/install-a-plugin.md), [Use ContextSeek](how-to/use-contextseek.md) |
| Build | Produce a deployable image or preview the build command. | [Build and deploy](how-to/build-and-deploy.md) |
| Deploy | Generate deployment manifests or run the project through Compose. | [Build and deploy](how-to/build-and-deploy.md), [Docker Compose](how-to/run-with-docker-compose.md) |
| Operate | Keep runtime data, paths, and integrations understandable after launch. | [Runtime data model](explanation/runtime-data-model.md), [File layout](reference/file-layout.md), [CLI reference](reference/cli.md) |

## How the stages fit together

`agentseek create` gives you a project surface with its own dependencies,
source tree, and `.env.example`. After that, most commands should run from the
generated project root, not from the AgentSeek repository checkout.

Configuration comes before local runs. At minimum, the project needs model
credentials. Add provider base URLs, MCP config, plugin settings, or storage
settings only when the chosen template or integration needs them.

Run modes are checkpoints for different questions. Use `agentseek chat` for a
simple model path, `agentseek gateway` for channel message handling, and
`agentseek run` for generated projects that include an app loop or frontend.
Use Docker Compose when the project or deployment path needs multiple services.

Extension work should stay inside the generated project unless you are changing
AgentSeek itself. Skills, MCP servers, plugins, ContextSeek, and contrib
packages are separate entry points so projects can grow without rewriting the
runtime core.

Build and deploy come after the project runs locally. The build command creates
or previews the image build, while deploy writes manifests that can be reviewed
before they are applied elsewhere.

Operation is mostly about keeping runtime data explainable. The runtime data
model explains what AgentSeek records, the file layout reference explains where
state lives, and the CLI reference lists the command surface when you need exact
flags.

## Starting points

- New project: start with [Build your first harness app](tutorials/02-first-harness-app.md).
- Choosing a starter: compare entries in [Templates](reference/templates.md) and [Hub](hub.md).
- Already generated a project: follow [Configure model](how-to/configure-model.md), then [Run locally](how-to/run-locally.md).
- Preparing for delivery: use [Build and deploy](how-to/build-and-deploy.md).
