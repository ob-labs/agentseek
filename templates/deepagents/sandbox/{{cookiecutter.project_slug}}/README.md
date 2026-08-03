# {{ cookiecutter.project_name }}

A sandbox-backed coding agent using DeepAgents + LangChain. It uses
[Daytona](https://docs.langchain.com/oss/python/integrations/sandboxes/daytona)
by default and supports
[LangSmith Sandbox](https://docs.langchain.com/langsmith/sandboxes) as an
alternative. See the
[sandbox integration index](https://docs.langchain.com/oss/python/integrations/sandboxes)
for the upstream integration overview.

## Configure Daytona

Requires **Python 3.12+**, [uv](https://docs.astral.sh/uv/), Node.js, and npm.

Create a Daytona API key in the [Daytona dashboard](https://app.daytona.io/).
Daytona currently advertises free compute for new accounts. Check
[current pricing](https://www.daytona.io/pricing) before relying on a specific
credit amount.

```bash
cp .env.example .env
$EDITOR .env
```

Set the default sandbox provider and API key in `.env`:

```dotenv
AGENTSEEK_SANDBOX_PROVIDER=daytona
DAYTONA_API_KEY=<your-daytona-api-key>
```

## Install and run

```bash
uvx agentseek task sync
uvx agentseek task frontend

uvx agentseek info
uvx agentseek doctor
uvx agentseek dev --dry-run
uvx agentseek dev
```

Use `uvx agentseek task --list` to see setup tasks. After the dev stack is
running, use `uvx agentseek doctor --live` to run the HTTP checks declared in
`.agentseek/lifecycle.toml`.

## Architecture

- **Backend**: `create_deep_agent` with graph ID `sandbox` and a selectable Daytona or LangSmith Sandbox backend, served by `langgraph dev` on port {{ cookiecutter.langgraph_port }}
- **Frontend**: React + Vite chat UI with streaming tool-call cards on port {{ cookiecutter.frontend_port }}

The agent can execute shell commands, read/write files, and interact with the
filesystem inside an isolated sandbox. A custom server lifespan performs
provider-specific cleanup during graceful shutdown, while `atexit` remains a
fallback. Stop it gracefully with Ctrl+C so the remote sandbox is deleted. If
a cleanup warning appears or the process is killed, check the provider
dashboard and delete any active sandbox manually.

## Workspace paths

For Daytona, the generated agent obtains the sandbox's writable directory with
`sandbox.get_work_dir()` and treats it as the root for file tools and commands.
For example, `hello.py` and `/hello.py` resolve to
`<daytona-work-dir>/hello.py` (normally `/home/daytona/hello.py`), never to
the host root `/hello.py`. Keep project files inside this workspace.
File tools report logical paths such as `/hello.py`; in shell commands, use
the workspace-relative form instead: `python hello.py`, not `python /hello.py`.

## Switch to LangSmith Sandbox

> **Billing:** LangSmith Sandbox is an alternative provider and its sandbox
> execution is charged. Check current LangSmith pricing before switching
> `AGENTSEEK_SANDBOX_PROVIDER` to `langsmith`.

Set the alternative provider and its API key in `.env`:

```dotenv
AGENTSEEK_SANDBOX_PROVIDER=langsmith
LANGSMITH_API_KEY=<your-langsmith-api-key>
```

## Environment

`.env` is read by the LangGraph backend and by AgentSeek readiness checks. It is
not a lifecycle process environment override.

- `AGENTSEEK_SANDBOX_PROVIDER` selects `daytona` (default) or `langsmith`.
- `DAYTONA_API_KEY` is required when the sandbox provider is `daytona`.
- `LANGSMITH_API_KEY` is required when the sandbox provider is `langsmith`.
- `AGENTSEEK_MODEL_PROVIDER` and `AGENTSEEK_MODEL` select the chat model and
  have scaffold-time defaults in `.agentseek/lifecycle.toml`.
- Set the API key for the selected provider: `OPENAI_API_KEY`,
  `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`.
- Optional base URL variables are only needed for compatible gateways.

Optional LangSmith tracing is independent of the sandbox provider. A
Daytona-backed agent can enable it without switching sandbox providers:

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-api-key>
LANGSMITH_PROJECT=my-sandbox-agent
```

For APAC or other non-default LangSmith regions, also set `LANGSMITH_ENDPOINT`
(e.g. `https://apac.api.smith.langchain.com`); otherwise traces may fail to
upload to the cloud.

The frontend reads `frontend/.env.example` values after copying them to
`frontend/.env` or when equivalent shell variables are present.
