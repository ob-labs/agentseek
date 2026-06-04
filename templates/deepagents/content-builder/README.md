# DeepAgents — content-builder template

Scaffolds a `deepagents.create_deep_agent(...)` content writing agent with
brand memory, skills, subagents, and image generation. Includes a LangGraph
backend and a Vite + React frontend that streams tool calls, sub-agent
delegation, a live DeepAgents todo panel, generated images, and the final
markdown output.

## Inputs

| Variable | Description |
| --- | --- |
| `project_name` | Human-readable project name. |
| `project_slug` | Python package / directory name (auto-derived). |
| `author` | Project author. |
| `default_model_provider` | Default `init_chat_model(..., model_provider=...)` provider. Ships as `openai`. |
| `default_model` | Default model id for the selected provider. Ships empty — user must set `AGENTSEEK_MODEL` in `.env`. |
| `google_image_model` | Gemini model for image generation. Ships as `gemini-3.1-flash-image-preview`. |
| `tavily_max_results` | Default `web_search` result limit. |
| `tavily_topic` | Tavily topic filter (`general` or `news`). |
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
  AGENTS.md
  subagents.yaml
  skills/
    blog-post/
      SKILL.md
    social-media/
      SKILL.md
  src/{{ project_slug }}/
    __init__.py
    agent.py
    tools.py
    webapp.py
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
      App.test.tsx
      TodoList.tsx
      ToolCallCard.tsx
      ToolCallCard.test.tsx
      ThinkingBlock.tsx
      ImageCard.tsx
      main.tsx
      styles.css
      vite-env.d.ts
```

## What's Adapted From Upstream

- Mirrors the upstream DeepAgents `content-builder-agent` example structure:
  AGENTS.md for brand voice, skills for blog/social workflows, subagents.yaml
  for a researcher with Tavily search, and image generation tools.
- Uses provider-first runtime config: generated apps select `openai`,
  `anthropic`, or `google_genai` in `.env`, then fill only the matching
  credential block.
- Treats blank provider base URLs as "use the official endpoint", while still
  allowing custom compatible gateways per provider.
- Lets generated apps override the scaffold-time model via `AGENTSEEK_MODEL`
  (plus `DEEPAGENTS_MODEL` / `BUB_MODEL` compatibility aliases) in `.env`.
- Image generation defaults to Google Gemini but supports custom endpoints via
  `GOOGLE_IMAGE_MODEL` and `GOOGLE_API_KEY` env vars.
- Adds a custom `/images/{path}` route via FastAPI so the frontend can display
  generated cover and social images inline.
- Adds a frontend for streamed tool/sub-agent visibility with an image preview
  component; upstream ships only the backend example.
- Surfaces DeepAgents `todos` state as a first-class progress panel instead of
  leaving planning updates buried in generic tool-call JSON.
