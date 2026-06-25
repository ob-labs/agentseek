# LangChain — default template

Scaffolds a `create_agent` project with CopilotKit middleware bound to
agentseek via `agentseek-langchain`, for local AG-UI development, and also
includes a first-class Feishu gateway path plus optional OpenTelemetry export
to Phoenix backed by SeekDB.

The generated project uses the AgentSeek dev lifecycle v1 contract:

```bash
agentseek info
agentseek doctor
agentseek dev --dry-run
agentseek dev
agentseek task --list
```

Lifecycle metadata lives in `.agentseek/lifecycle.toml`. Gateway,
CopilotKit, and frontend service URLs plus HTTP live checks are declared there;
the template does not require CLI/core changes for those checks.

## Architecture

```text
Browser (CopilotKit v2)
  -> Vite dev server :{{ frontend_port }}  (/api/copilotkit/* proxied)
    -> Copilot Runtime (Express) :{{ copilotkit_port }}  /api/copilotkit
      -> HttpAgent (AG-UI client)
        -> bub gateway :{{ gateway_port }}  /agent  (AG-UI channel)
          -> agentseek-langchain messages_spec(...)
            -> create_agent(...) + CopilotKitMiddleware
              -> OpenTelemetry spans -> Phoenix :6006/v1/traces -> SeekDB
```

| LangChain guide | Generated project | Conversion point |
| --- | --- | --- |
| `create_agent(...)` + `CopilotKitState` + `CopilotKitMiddleware` | `demo_binding.py` | None |
| `normalize_context` + `apply_structured_output_schema` | `middleware.py` | None |
| `langgraph.json` + `http.app` custom endpoint | `bub gateway --enable-channel ag-ui` + `build_spec()` | FastAPI endpoint replaced by `messages_spec(...)` |

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name. |
| `author` | Project author. |
| `system_prompt` | System prompt baked into the agent. |
| `default_model` | Default `BUB_MODEL`. |
| `gateway_port` | Default gateway port for AG-UI. |
| `frontend_port` | Vite dev server port for the frontend. |
| `copilotkit_port` | CopilotKit Express runtime port. |

## Generated layout

```
{{ project_slug }}/
  .agentseek/
    lifecycle.toml
  README.md
  pyproject.toml
  requirements.txt
  Dockerfile
  docker-compose.yml
  .env.example
  src/{{ project_slug }}/
    __init__.py
    demo_binding.py
    middleware.py
    observability.py
    settings.py
    feishu.py
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
      langchainCopilotKitUi.tsx
      main.tsx
      style.css
      vite-env.d.ts
```

## Key code patterns

The backend binding keeps the standard LangChain agent shape and swaps only
the transport layer:

```python
from agentseek_langchain import messages_spec

def build_spec():
    return messages_spec(build_agent(), include_agents_md=True)
```

The middleware follows the CopilotKit guide pattern: normalize context, then
turn `output_schema` into LangChain structured output. The frontend uses
Hashbrown to parse assistant JSON into React components.

OpenTelemetry support is registered inside the generated LangChain application,
not inside Bub or the message forwarding layer:

```python
from .observability import configure_tracing

def build_agent():
    settings = get_settings()
    configure_tracing(settings)
    return create_agent(...)
```

The generated `docker-compose.yml` is the default lifecycle stack: it starts
Bub gateway, the CopilotKit frontend, Phoenix, and a SeekDB backend in one
`agentseek dev` run. Phoenix uses
`PHOENIX_SQL_DATABASE_URL=mysql://root@seekdb:2881/phoenix` and persists data in
`quay.io/oceanbase/seekdb:latest`. Its optional `feishu` profile starts the
Feishu gateway with the same LangChain spec and environment surface; enable it
with `COMPOSE_PROFILES=feishu` in `.env`.
