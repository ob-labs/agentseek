# Bub — default template

Scaffolds a minimal Bub-flavored agent project: an AG-UI gateway plus a
CopilotKit-based frontend that streams messages through it. No LangChain
layer is required.

## Architecture

```text
Browser (CopilotKit v2)
  -> Vite dev server :{{ frontend_port }}  (/api/copilotkit/* proxied)
    -> Copilot Runtime (Express) :4000  /api/copilotkit
      -> HttpAgent (AG-UI client)
        -> agentseek gateway :{{ gateway_port }}  /agent  (AG-UI channel)
          -> configured agentseek model provider
```

Two processes start via `concurrently`:

| Process | Default port | Role |
| --- | --- | --- |
| `tsx server.ts` | `4000` | CopilotKit runtime (`CopilotRuntime` + `createCopilotExpressHandler`). |
| `vite` | `{{ frontend_port }}` | React app; proxies `/api/copilotkit` to the runtime. |

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Project / directory name. |
| `author` | Project author. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `gateway_port` | Default port for `agentseek gateway`. |
| `frontend_port` | Vite dev server port for the frontend. |

## Generated layout

```
{{ project_slug }}/
  README.md
  pyproject.toml
  Dockerfile
  .env.example
  src/{{ project_slug }}/
    __init__.py
    dev.py
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
| `AGENTSEEK_MODEL` | — | Model id for the gateway (e.g. `openai:gpt-4o-mini`). |
| `AGENTSEEK_STREAM_OUTPUT` | `false` | Set `true` for token-by-token streaming in the gateway. |
| `COPILOTKIT_PORT` | `4000` | Port for the Express Copilot runtime. |
| `AGENTSEEK_AG_UI_AGENT_URL` | `http://127.0.0.1:{{ gateway_port }}/agent` | URL passed to `HttpAgent`; must match the gateway AG-UI endpoint. |
