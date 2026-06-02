# DeepAgents — research template

Scaffolds a pure `deepagents.create_deep_agent(...)` research project with a
LangGraph backend and a Vite + React frontend that streams tool calls,
sub-agent delegation, and the final markdown report.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name (auto-derived). |
| `author` | Project author. |
| `default_model` | Default `init_chat_model("<provider>:<model>")` id. Ships as `openai:Pro/zai-org/GLM-5.1`. |
| `tavily_max_results` | Default `tavily_search` result limit. |
| `tavily_topic` | Tavily topic filter (`general`, `news`, or `finance`). |
| `max_concurrent_research_units` | Max sub-agent tasks the orchestrator may queue concurrently. |
| `max_researcher_iterations` | Max search/reflection loops per research unit. |
| `langgraph_port` | Default backend port for `langgraph dev`. |
| `frontend_port` | Default Vite dev-server port. |

## Generated layout

```text
{{ project_slug }}/
  README.md
  pyproject.toml
  langgraph.json
  .env.example
  .gitignore
  src/{{ project_slug }}/
    __init__.py
    agent.py
    prompts.py
    tools.py
  frontend/
    package.json
    .env.example
    .gitignore
    index.html
    vite.config.ts
    tsconfig.json
    tsconfig.node.json
    src/
      App.tsx
      ToolCallCard.tsx
      main.tsx
      styles.css
      vite-env.d.ts
```

## What's Adapted From Upstream

- Mirrors the upstream DeepAgents `deep_research` prompt structure and Tavily +
  `think_tool` workflow.
- Uses `init_chat_model("openai:...")` plus the `AGENTSEEK_*` to `OPENAI_*`
  env bridge so OpenAI-compatible endpoints work with the template defaults.
- Defaults to `openai:Pro/zai-org/GLM-5.1` because that path was verified
  end-to-end against the SiliconFlow-compatible backend for sub-agent streaming.
- Adds a frontend for streamed tool/sub-agent visibility; upstream ships only
  the backend example.
