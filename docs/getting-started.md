# Getting Started

This tutorial gets agentseek running locally with SQLite-backed runtime storage. It assumes Python 3.12+ and `uv` are already available.

## 1. Install

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

## 2. Configure

Use `AGENTSEEK_*` variables for the agentseek distribution. They are passed through to Bub as `BUB_*` aliases.

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
export AGENTSEEK_TAPESTORE_SQLALCHEMY_URL=sqlite+pysqlite:///./agentseek-tapes.db
```

The SQLite file is created automatically on first use.

## 3. Run

```bash
uv run agentseek chat
```

You should see an interactive chat session. The example API key is a placeholder; use a real key before expecting model responses.

## 4. Check Local State

agentseek stores local config and runtime state under `.agentseek` in the current workspace by default.

Set `AGENTSEEK_HOME` or `BUB_HOME` to use another location.

## Next

- Run `uv run agentseek onboard` to collect configuration interactively.
- Use `uv run bub ...` when you want the upstream Bub CLI directly.
- See [Configuration](configuration.md) for environment variables, storage, and channel settings.
