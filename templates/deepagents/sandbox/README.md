# deepagents/sandbox

Cookiecutter template for a **sandbox-backed coding agent** using
[DeepAgents](https://docs.langchain.com/oss/deepagents) +
[LangChain](https://docs.langchain.com/oss/langchain). It uses
[Daytona](https://docs.langchain.com/oss/python/integrations/sandboxes/daytona)
by default and supports
[LangSmith Sandbox](https://docs.langchain.com/langsmith/sandboxes) as an
alternative. See the
[sandbox integration index](https://docs.langchain.com/oss/python/integrations/sandboxes)
for the upstream integration overview.

The generated project includes:

- **Backend** — a `create_deep_agent` graph with the `sandbox` graph ID and a
  selectable Daytona or LangSmith Sandbox backend, served by `langgraph dev`.
  The agent can execute shell commands, read/write files, and interact with the
  filesystem inside an isolated sandbox.
- **Frontend** — React + Vite chat UI with streaming tool-call cards, join &
  rejoin support for long-running sandbox tasks, and markdown rendering.
- **Lifecycle** — an AgentSeek lifecycle v1 spec for `info`, `doctor`, `dev`,
  and project setup tasks.

## Prerequisites

This template requires **Python 3.12+** and uses [uv](https://docs.astral.sh/uv/)
for dependency management. Install uv first:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create a Daytona API key in the [Daytona dashboard](https://app.daytona.io/).
Daytona currently advertises free compute for new accounts. Check
[current pricing](https://www.daytona.io/pricing) before relying on a specific
credit amount.

After you copy `.env.example` to `.env`, configure the default provider:

```dotenv
AGENTSEEK_SANDBOX_PROVIDER=daytona
DAYTONA_API_KEY=<your-daytona-api-key>
```

## Quick start

```bash
# 1. Scaffold
uvx cookiecutter templates/deepagents/sandbox

# 2. Configure
cd <project_slug>
cp .env.example .env
$EDITOR .env

# 3. Install project dependencies
uvx agentseek task sync
uvx agentseek task frontend

# 4. Inspect, check, and run the lifecycle
uvx agentseek info
uvx agentseek doctor
uvx agentseek dev --dry-run
uvx agentseek dev
```

Run `uvx agentseek task --list` from the generated project to see setup tasks.
Live HTTP checks are declared only in `.agentseek/lifecycle.toml` and run with
`uvx agentseek doctor --live` after `uvx agentseek dev` is running.

## Switch to LangSmith Sandbox

> **Billing:** LangSmith Sandbox is an alternative provider and its sandbox
> execution is charged. Check current LangSmith pricing before switching
> `AGENTSEEK_SANDBOX_PROVIDER` to `langsmith`.

Set the alternative provider and its API key in `.env`:

```dotenv
AGENTSEEK_SANDBOX_PROVIDER=langsmith
LANGSMITH_API_KEY=<your-langsmith-api-key>
```

Optional LangSmith tracing is independent of the selected sandbox provider.
For example, a Daytona-backed agent can enable tracing separately:

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-api-key>
LANGSMITH_PROJECT=my-sandbox-agent
```

## Sandbox cleanup

The generated custom server lifespan performs provider-specific cleanup during
graceful shutdown, while `atexit` remains a fallback. Stop `uvx agentseek dev`
gracefully with Ctrl+C so the remote sandbox is deleted. If a cleanup warning
appears or the process is killed, check the provider dashboard and delete any
active sandbox manually.

## Cookiecutter variables

| Variable                 | Default            | Description                          |
| ------------------------ | ------------------ | ------------------------------------ |
| `project_name`           | Sandbox Coding Agent | Human-readable name               |
| `project_slug`           | *(derived)*        | Python package / directory name      |
| `author`                 | Your Name          | Author for pyproject.toml            |
| `default_model_provider` | openai             | openai / anthropic / google_genai    |
| `default_model`          | gpt-4.1-mini       | Model ID for the chosen provider     |
| `langgraph_port`         | 2024               | Backend dev server port              |
| `frontend_port`          | 5175               | Frontend Vite dev server port        |
