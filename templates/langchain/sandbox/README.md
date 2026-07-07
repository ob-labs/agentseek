# langchain/sandbox

Cookiecutter template for a **sandbox-backed coding agent** using
[DeepAgents](https://docs.langchain.com/oss/deepagents) +
[LangChain](https://docs.langchain.com/oss/langchain) with a
[LangSmith Sandbox](https://docs.langchain.com/langsmith/sandboxes) backend.

The generated project includes:

- **Backend** — a `create_deep_agent` graph with a LangSmith sandbox backend,
  served by `langgraph dev`. The agent can execute shell commands, read/write
  files, and interact with the filesystem inside an isolated sandbox.
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

## Quick start

```bash
# 1. Scaffold
uvx cookiecutter templates/langchain/sandbox

# 2. Configure
cd <project_slug>
cp .env.example .env
$EDITOR .env

# 3. Install project dependencies
uvx agentseek task backend
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
