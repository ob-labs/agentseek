# {{ cookiecutter.project_name }}

A sandbox-backed coding agent using DeepAgents + LangChain with a LangSmith sandbox backend.

## Setup

Requires **Python 3.12+**, [uv](https://docs.astral.sh/uv/), Node.js, and npm.

```bash
cp .env.example .env
$EDITOR .env

uvx agentseek task backend
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

- **Backend**: `create_deep_agent` with a LangSmith sandbox backend, served by `langgraph dev` on port {{ cookiecutter.langgraph_port }}
- **Frontend**: React + Vite chat UI with streaming tool-call cards on port {{ cookiecutter.frontend_port }}

The agent can execute shell commands, read/write files, and interact with the filesystem inside an isolated LangSmith sandbox. The sandbox is automatically cleaned up when the backend shuts down gracefully (Ctrl+C).

## Environment

`.env` is read by the LangGraph backend and by AgentSeek readiness checks. It is
not a lifecycle process environment override.

- `LANGSMITH_API_KEY` is required for the sandbox backend.
- `AGENTSEEK_MODEL_PROVIDER` and `AGENTSEEK_MODEL` select the chat model and
  have scaffold-time defaults in `.agentseek/lifecycle.toml`.
- Set the API key for the selected provider: `OPENAI_API_KEY`,
  `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`.
- Optional base URL variables are only needed for compatible gateways.

The frontend reads `frontend/.env.example` values after copying them to
`frontend/.env` or when equivalent shell variables are present.
