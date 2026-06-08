# LangChain — default template

Scaffolds a `create_agent` project with CopilotKit middleware bound to
agentseek via `agentseek-langchain`, for local AG-UI development, and also
includes a first-class Feishu gateway path.

## Architecture

```text
Browser (CopilotKit v2)
  -> Vite dev server :{{ frontend_port }}  (/api/copilotkit/* proxied)
    -> Copilot Runtime (Express) :{{ copilotkit_port }}  /api/copilotkit
      -> HttpAgent (AG-UI client)
        -> agentseek gateway :{{ gateway_port }}  /agent  (AG-UI channel)
          -> agentseek-langchain messages_spec(...)
            -> create_agent(...) + CopilotKitMiddleware
```

| LangChain guide | Generated project | Conversion point |
| --- | --- | --- |
| `create_agent(...)` + `CopilotKitState` + `CopilotKitMiddleware` | `demo_binding.py` | None |
| `normalize_context` + `apply_structured_output_schema` | `middleware.py` | None |
| `langgraph.json` + `http.app` custom endpoint | `agentseek gateway --enable-channel ag-ui` + `build_spec()` | FastAPI endpoint replaced by `messages_spec(...)` |

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name. |
| `author` | Project author. |
| `system_prompt` | System prompt baked into the agent. |
| `default_model` | Default `AGENTSEEK_MODEL`. |
| `gateway_port` | Default gateway port for AG-UI. |
| `frontend_port` | Vite dev server port for the frontend. |
| `copilotkit_port` | CopilotKit Express runtime port. |

## Generated layout

```
{{ project_slug }}/
  README.md
  pyproject.toml
  requirements.txt
  Dockerfile
  .env.example
  src/{{ project_slug }}/
    __init__.py
    demo_binding.py
    middleware.py
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
