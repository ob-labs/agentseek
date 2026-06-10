# {{ cookiecutter.project_name }}

DeepAgents content builder scaffolded with
`agentseek create deepagents/content-builder`.

The backend serves a `create_deep_agent(...)` graph through `langgraph dev`
with brand-voice memory, content skills (blog-post, social-media), a
researcher subagent, and image generation tools. The frontend streams user
messages, tool calls, sub-agent delegation, generated images, and the final
markdown output.

## Setup

```bash
uv sync
npm install --prefix frontend

cp .env.example .env
cp frontend/.env.example frontend/.env
# Fill in backend secrets in .env:
# - Set AGENTSEEK_MODEL_PROVIDER and AGENTSEEK_MODEL
# - Fill only the matching provider block
# - If you switch providers, switch AGENTSEEK_MODEL to that provider's model id
# - Leave that provider's base URL empty to use the official endpoint
# - Set GOOGLE_API_KEY (required for image generation)
# - Set TAVILY_API_KEY (required for researcher subagent)
# - Optionally set AGENTSEEK_SUBAGENT_MODEL to override the researcher model
# - Optionally set GOOGLE_IMAGE_MODEL to use a different Gemini image model
# frontend/.env only needs changes if you want a non-default LangGraph URL.
```

`agent.py` uses `AGENTSEEK_MODEL_PROVIDER` to choose a native LangChain
provider integration for OpenAI, Anthropic, or Gemini. Fill only that
provider's env block in `.env`; if its base URL is blank, the generated app
uses the provider's official default endpoint. You can also override the
scaffolded model name via `AGENTSEEK_MODEL` (or the compatibility aliases
`DEEPAGENTS_MODEL` / `BUB_MODEL`) without editing code.

The researcher subagent shares the same provider and base URL as the main
model. To use a smaller/cheaper model for research, set
`AGENTSEEK_SUBAGENT_MODEL` to just the model name (e.g. `gpt-4.1-mini`) —
no provider prefix needed.

## Run

Start the backend:

```bash
uv run langgraph dev --port {{ cookiecutter.langgraph_port }} --no-browser
```

Start the frontend in a second terminal:

```bash
npm run --prefix frontend dev
```

By default the backend listens on
`http://127.0.0.1:{{ cookiecutter.langgraph_port }}` and the frontend on
`http://127.0.0.1:{{ cookiecutter.frontend_port }}`.

## Smoke test

Open `http://127.0.0.1:{{ cookiecutter.frontend_port }}` and ask:

```text
Write a blog post about how AI agents are transforming software development
```

Expected behavior:

- A live **Content plan** todo panel appears when the agent writes todos.
- Tool cards appear for `web_search` and, when the model delegates,
  `task` as a "Sub-agent: researcher" card.
- Image cards display the generated cover image inline after
  `generate_cover` completes.
- Each tool card expands while running, then collapses after its result
  lands.
- The final assistant response renders as markdown.

## Customization

- Edit `AGENTS.md` to change brand voice and writing standards.
- Add or modify skills under `skills/<name>/SKILL.md` for new content types.
- Add subagents in `subagents.yaml` and register their tools in `agent.py`.
- Set `GOOGLE_IMAGE_MODEL` in `.env` to use a different Gemini model for images.
- Generated content is written to `blogs/`, `linkedin/`, `tweets/`, and
  `research/` directories under the project root.
