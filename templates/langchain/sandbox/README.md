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

# 2. Backend
cd <project_slug>
cp .env.example .env        # fill in API keys
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e .
langgraph dev --no-browser

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

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
