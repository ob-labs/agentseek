# Bub — default template

Scaffolds a Bub AG-UI project with an AgentSeek lifecycle file. The generated
runtime depends on `bub==0.3.9` plus the AG-UI Bub channel plugin; `duty` is a
dev dependency for direct local task-runner usage, while AgentSeek brings its
own duty execution layer.

## Architecture

```text
uvx agentseek dev
  -> duties.py
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

Additional project tasks can be exposed with `@duty` in `duties.py` and run
through `uvx agentseek task <name>`.

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
  .env.example
  duties.py
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
| `BUB_AG_UI_AGENT_URL` | `http://127.0.0.1:{{ gateway_port }}/agent` | URL used by the Copilot Runtime HttpAgent. |
