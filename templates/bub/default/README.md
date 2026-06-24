# Bub — default template

Scaffolds a Bub AG-UI project with an AgentSeek lifecycle spec. The generated
runtime depends on `bub==0.3.9` plus the AG-UI Bub channel plugin and includes
an optional gateway Dockerfile.

## Architecture

```text
uvx agentseek dev
  -> .agentseek/lifecycle.toml
    -> uv run bub gateway --enable-channel ag-ui
        -> BubFramework + ag-ui channel :{{ gateway_port }} /agent
    -> Vite dev server :{{ frontend_port }} (/api/copilotkit/* proxied)
        -> Copilot Runtime :{{ copilotkit_port }} /api/copilotkit
```

Two long-running processes start in development:

| Process | Default port | Role |
| --- | --- | --- |
| `uv run bub gateway --enable-channel ag-ui` | `{{ gateway_port }}` | Starts the Bub AG-UI gateway. |
| `npm run dev` | `{{ frontend_port }}` / `{{ copilotkit_port }}` | Starts the Vite app and Copilot Runtime. |

Additional project tasks can be declared in `.agentseek/lifecycle.toml` and
run through `uvx agentseek task <name>`.

AgentSeek reads `.env` for readiness and lifecycle env requirements. Runtime
environment ownership stays with the spawned processes: Bub and the AG-UI
channel read the project `.env`, the Vite app reads frontend env files and the
Copilot Runtime reads its shell environment or built-in defaults.

Generated projects use the lifecycle commands directly:

```bash
uvx agentseek info
uvx agentseek doctor
uvx agentseek dev --dry-run
uvx agentseek dev
uvx agentseek task --list
```

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Project / directory name. |
| `author` | Project author. |
| `default_model` | Default `BUB_MODEL`. |
| `gateway_port` | Default port for the Bub AG-UI gateway. |
| `frontend_port` | Vite dev server port for the frontend. |
| `copilotkit_port` | CopilotKit Express runtime port. |

## Generated layout

```
{{ project_slug }}/
  README.md
  pyproject.toml
  Dockerfile
  .agentseek/lifecycle.toml
  .env.example
  src/{{ project_slug }}/
    __init__.py
  frontend/
    README.md
    .env.example
    index.html
    package.json
    server.ts
    vite.config.ts
    tsconfig.json
    src/
      App.tsx
      main.tsx
      style.css
      vite-env.d.ts
```

## Key runtime variables

| Variable | Default | Meaning |
| --- | --- | --- |
| `BUB_MODEL` | `{{ default_model }}` | Model id used by Bub. |
| `BUB_API_KEY` | — | Generic model provider key. |
| `BUB_OPENAI_API_KEY` | — | Provider-specific key when `BUB_MODEL` uses `openai:`. |
| `BUB_STREAM_OUTPUT` | `true` | Enables token-by-token output in the Bub channel manager. |
| `BUB_AG_UI_PORT` | `{{ gateway_port }}` | Bub AG-UI gateway port. |
| `BUB_AG_UI_AGENT_URL` | `http://127.0.0.1:{{ gateway_port }}/agent` | URL used by the Copilot Runtime HttpAgent. |
| `COPILOTKIT_PORT` | `{{ copilotkit_port }}` | Port for the Express Copilot Runtime. |
