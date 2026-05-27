# Contributing a template

This directory holds [cookiecutter](https://cookiecutter.readthedocs.io/) projects that `agentseek create` scaffolds for users. Templates are discovered by `_local_templates_root()` in `contrib/agentseek-cli/src/agentseek_cli/commands/create.py`; the CLI resolves `<type>/<name>` to `templates/<type>/<name>/`.

## Layout

```
templates/<type>/<name>/
  cookiecutter.json                       # variables prompted on generation
  README.md                               # human-readable description (see "Required README sections")
  {{cookiecutter.project_slug}}/          # the rendered project tree
    pyproject.toml
    .env.example
    src/{{cookiecutter.project_slug}}/    # Python package, if applicable
    frontend/                             # Vite/TS frontend, if applicable
```

Jinja substitution is active inside file contents and inside directory/file names.

## Naming convention

- `<type>` is one of `bub`, `deepagents`, `langchain` (the values in `KNOWN_TYPES` at `contrib/agentseek-cli/src/agentseek_cli/commands/create.py`).
- `<name>` is descriptive (`markdown-messages`, `research`, `skills`), not generic.
- The name `default` is reserved for the **agentseek-wrapped** variant when a type ships both wrapped and pure variants. New templates should pick a descriptive name; do not introduce more `default` templates.
- When a type has both a wrapped and a pure variant of the same pattern, suffix the non-canonical one with `-agentseek` or `-pure`. The canonical (unsuffixed) form is the one we expect most users to start from.

## Required files

Every template directory must contain:

1. `cookiecutter.json` — at minimum `project_name`, `project_slug`, `author`. Add `default_model` when the template uses an LLM. Always provide sensible defaults; `--no-input` users will get them verbatim.
2. `README.md` next to `cookiecutter.json` — describes inputs and points at the generated project.
3. `{{cookiecutter.project_slug}}/README.md` — describes how to run the generated project. Two-terminal commands, env vars required, smoke check.
4. `{{cookiecutter.project_slug}}/.env.example` — lists every env var the generated project reads, with safe defaults from cookiecutter vars where applicable.
5. `{{cookiecutter.project_slug}}/pyproject.toml` — `requires-python = ">=3.12"`, explicit dependencies.

## Required README sections

The template's `README.md` (next to `cookiecutter.json`) must include:

- **Inputs** — a markdown table of every cookiecutter variable with a one-line description.
- **Generated layout** — a tree of what `agentseek create <type>/<name>` produces.

The generated project's `README.md` (inside `{{cookiecutter.project_slug}}/`) must include:

- **Setup** — the exact commands a user runs after `agentseek create`.
- **Run** — how to start the agent and, if applicable, the frontend.
- **Smoke test** — one concrete command or click-path that proves the project works.

## Pure vs agentseek-wrapped templates

A template is "pure" when the generated project has no `agentseek-langchain` or `agentseek-ag-ui` dependency and does not call `messages_spec(...)`. A template is "agentseek-wrapped" when it does.

Pure templates should look as close as possible to the upstream LangChain / DeepAgents example they mirror, so a developer reading those docs can drop into our template without surprise.

### `.env` + `init_chat_model` (pure templates)

Pure templates use `.env` + `init_chat_model` directly. If you want users with an `AGENTSEEK_API_KEY` / `AGENTSEEK_API_BASE` in their `.env` to "just work" with `init_chat_model("openai:...")`, copy this 4-line bridge near the top of the agent module (after `load_dotenv()`):

```python
import os
if os.getenv("AGENTSEEK_API_KEY") and not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = os.environ["AGENTSEEK_API_KEY"]
if os.getenv("AGENTSEEK_API_BASE") and not os.getenv("OPENAI_API_BASE"):
    os.environ["OPENAI_API_BASE"] = os.environ["AGENTSEEK_API_BASE"]
```

Document `OPENAI_API_KEY` (and any other provider key) in `.env.example` — the bridge is convenience, not a substitute for users knowing what `init_chat_model` reads.

### `build_spec()` factory (agentseek-wrapped templates)

Agentseek-wrapped templates must expose a `build_spec()` factory that returns a `RunnableSpec`. This is what `AGENTSEEK_LANGCHAIN_SPEC` loads. Keep it isolated at the bottom of the agent module, clearly separated from the LangChain core, so a reader can see the whole agentseek surface in one block:

```python
def build_agent():
    # ... LangChain code, identical to the pure variant ...
    return create_deep_agent(model=model, tools=[...], system_prompt="...")


# --- agentseek binding ------------------------------------------------------
# build_spec() is what AGENTSEEK_LANGCHAIN_SPEC loads. Delete this block and
# you have a vanilla DeepAgents project.
from agentseek_langchain import messages_spec  # noqa: E402
def build_spec():
    return messages_spec(build_agent(), include_agents_md=True)
```

The `# noqa: E402` suppresses ruff's "module-level import not at top of file" warning — the late import is intentional so the binding can be deleted as a single block to recover a vanilla project.

The wrapped template's README must include a **"What's different vs. pure"** section listing exactly the lines that differ (typically: two added imports, one factory, one dependency in `pyproject.toml`).

## After adding a template

1. Add an entry to `templates/index.json` keyed by `<type>/<name>` with a one-line description.
2. Run the render check: `uv run --package agentseek-cli pytest contrib/agentseek-cli/tests/test_templates_render.py -v`. Your template should appear as a new parametrize case and pass.
3. Run `agentseek create <type>/<name> --no-input` in a scratch directory and inspect the output by hand.
