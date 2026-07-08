# DeepAgents — research template

Scaffolds a pure `deepagents.create_deep_agent(...)` research project with a
LangGraph backend and a Vite + React frontend that streams tool calls,
sub-agent delegation, a live DeepAgents todo panel, and the final markdown
report.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name (auto-derived). |
| `author` | Project author. |
| `default_model_provider` | Default `init_chat_model(..., model_provider=...)` provider. Ships as `openai`. |
| `default_model` | Default model id for the selected provider. Ships as `gpt-4.1-mini`. |
| `tavily_max_results` | Default `tavily_search` result limit. |
| `tavily_topic` | Tavily topic filter (`general`, `news`, or `finance`). |
| `max_concurrent_research_units` | Max sub-agent tasks the orchestrator may queue concurrently. |
| `max_researcher_iterations` | Max search/reflection loops per research unit. |
| `langgraph_port` | Default backend port for `langgraph dev`. |
| `frontend_port` | Default Vite dev-server port. |

## Generated layout

```text
{{ project_slug }}/
  .agentseek/
    lifecycle.toml
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
      TodoList.tsx
      ToolCallCard.tsx
      main.tsx
      styles.css
      vite-env.d.ts
```

## What's Adapted From Upstream

- Mirrors the upstream DeepAgents `deep_research` prompt structure and Tavily +
  `think_tool` workflow.
- Uses provider-first runtime config: generated apps select `openai`,
  `anthropic`, or `google_genai` in `.env`, then fill only the matching
  credential block.
- Declares AgentSeek dev lifecycle v1 in `.agentseek/lifecycle.toml`, including
  `info`, `doctor`, `dev`, and `task` entry points for local development.
- Treats blank provider base URLs as "use the official endpoint", while still
  allowing custom compatible gateways per provider.
- Lets generated apps override the scaffold-time model via `AGENTSEEK_MODEL`
  (plus `DEEPAGENTS_MODEL` / `BUB_MODEL` compatibility aliases) in `.env`.
- Defaults to provider `openai` with model `gpt-4.1-mini` so a fresh scaffold
  works against the official OpenAI endpoint when `OPENAI_API_BASE` is blank.
- Still supports OpenAI-compatible gateways by pointing `OPENAI_API_BASE` at
  the compatible endpoint and swapping `AGENTSEEK_MODEL` to a model that
  gateway actually serves.
- Adds a frontend for streamed tool/sub-agent visibility; upstream ships only
  the backend example.
- Surfaces DeepAgents `todos` state as a first-class progress panel instead of
  leaving planning updates buried in generic tool-call JSON.
