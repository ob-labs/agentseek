# langchain/markdown-messages

Scaffolds a pure LangChain `create_agent` project served by `langgraph dev`,
with a Vite + React frontend that streams messages via `useStream` and renders
them as markdown.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. Defaults to "Markdown Messages Agent". |
| `project_slug` | Python package / directory name (auto-derived). |
| `author` | Project author. |
| `system_prompt` | System prompt baked into the agent. |
| `default_model` | Fallback model id used when `AGENTSEEK_MODEL` / `OPENAI_MODEL` is not set. Defaults to `openai:qwen3-max`. |
| `langgraph_port` | Backend port for `langgraph dev`. Defaults to `2024`. |
| `frontend_port` | Frontend dev-server port. Defaults to `5174`. |

## Generated layout

```text
{{ project_slug }}/
  .agentseek/lifecycle.toml
  README.md
  pyproject.toml
  langgraph.json
  .env.example
  .gitignore
  src/{{ project_slug }}/
    __init__.py
    agent.py
  frontend/
    package.json
    .env.example
    .gitignore
    index.html
    tsconfig.json
    tsconfig.node.json
    vite.config.ts
    src/
      App.tsx
      main.tsx
      styles.css
      vite-env.d.ts
```

## Notes

- Pure template: no `agentseek-langchain`, `agentseek-ag-ui`, or runtime wrapper.
- Generated projects expose AgentSeek lifecycle v1 through
  `.agentseek/lifecycle.toml`.
- Backend uses the documented `AGENTSEEK_*` to `OPENAI_*` `.env` bridge so either
  credential pair works with OpenAI-compatible providers. `AGENTSEEK_MODEL` or
  `OPENAI_MODEL` selects the runtime model and overrides the cookiecutter
  fallback.
- Frontend pins `@langchain/react` to `~0.3.5`, which is the working line for
  the `langgraph-cli[inmem]` server used by this template.
