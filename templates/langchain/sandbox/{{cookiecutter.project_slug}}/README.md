# {{ cookiecutter.project_name }}

A sandbox-backed coding agent using DeepAgents + LangChain with a LangSmith sandbox backend.

## Setup

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/).

```bash
# Create venv and install dependencies
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start backend (use --no-browser to skip auto-opening LangSmith Studio)
langgraph dev --no-browser

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

## Architecture

- **Backend**: `create_deep_agent` with a LangSmith sandbox backend, served by `langgraph dev` on port {{ cookiecutter.langgraph_port }}
- **Frontend**: React + Vite chat UI with streaming tool-call cards on port {{ cookiecutter.frontend_port }}

The agent can execute shell commands, read/write files, and interact with the filesystem inside an isolated LangSmith sandbox. The sandbox is automatically cleaned up when the backend shuts down gracefully (Ctrl+C).
