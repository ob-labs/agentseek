# {{ cookiecutter.project_name }}

DeepAgents content builder scaffolded with
`agentseek create deepagents/content-builder`.

The backend serves a `create_deep_agent(...)` graph through `langgraph dev`
with brand-voice memory, content skills (blog-post, social-media), a
researcher subagent, and image generation tools. The frontend streams user
messages, tool calls, sub-agent delegation, generated images, and the final
markdown output. AgentSeek is used as the external lifecycle tool for local
inspection, readiness checks, development, and project tasks.

## Setup

```bash
uv sync

cp .env.example .env
cp frontend/.env.example frontend/.env
$EDITOR .env

agentseek task frontend
agentseek info
agentseek doctor
agentseek dev
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

## Environment

The root `.env` is referenced by both `langgraph.json` and
`.agentseek/lifecycle.toml`. LangGraph loads it for the backend process;
AgentSeek reads it for `doctor` readiness checks. Shell environment variables
still take precedence when present.

The frontend has its own `frontend/.env`. It only needs changes when the
LangGraph URL or frontend port differs from the scaffold defaults.

For the default OpenAI provider, set `AGENTSEEK_MODEL` and `OPENAI_API_KEY`.
`DEEPAGENTS_MODEL` or `BUB_MODEL` can be used as model aliases, and
`BUB_OPENAI_API_KEY` can be used as an OpenAI key alias. If you switch
providers, update `AGENTSEEK_MODEL_PROVIDER`, use a model id for that provider,
and fill the matching provider key. Leave provider base URLs empty to use the
official endpoints.

`TAVILY_API_KEY` enables the researcher subagent. `GOOGLE_API_KEY` is required
for image generation and also for `google_genai` chat models.

## Lifecycle

```bash
agentseek info
agentseek doctor
agentseek dev
agentseek task --list
```

By default the backend listens on
`http://127.0.0.1:{{ cookiecutter.langgraph_port }}` and the frontend on
`http://127.0.0.1:{{ cookiecutter.frontend_port }}`. Runtime processes and
project tasks are declared in `.agentseek/lifecycle.toml`.

After `agentseek dev` starts, open the frontend and ask:

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
