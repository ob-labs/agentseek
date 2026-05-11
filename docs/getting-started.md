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

If you want SQLAlchemy-backed tape storage, install the optional OceanBase tape store plugin first:

```bash
uv sync --extra oceanbase
```

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
export AGENTSEEK_TAPESTORE_SQLALCHEMY_URL=sqlite+pysqlite:///./agentseek-tapes.db
```

The SQLite file is created automatically on first use.
If you later switch the same setting to an OceanBase URL, the optional tape store plugin can also enable vector retrieval through `pyobvector`.

## 3. Run

```bash
uv run agentseek chat
```

You should see an interactive chat session. The example API key is a placeholder; use a real key before expecting model responses.

## 4. Check Local State

agentseek stores local config and runtime state under `.agentseek` in the current workspace by default.

Set `AGENTSEEK_HOME` or `BUB_HOME` to use another location.

## 5. Local Skills And MCP

Project-local skills can live under:

```text
.agents/skills
```

Bub discovers that path from the workspace automatically, so local `agentseek` runs can use those skills without extra wiring.

For MCP, `bub-mcp` reads `${BUB_HOME}/mcp.json` by default. With agentseek defaults, that means:

```text
.agentseek/mcp.json
```

If you prefer a project-level MCP file such as `.agents/mcp.json`, set `AGENTSEEK_MCP_CONFIG_PATH` explicitly before starting the CLI.

## 6. Docker Compose

If you want to run `agentseek` in a container with the current workspace mounted in, the repository already includes `docker-compose.yml`:

```bash
cp .env.example .env
make compose-up
```

This mode mounts the current repository into `/workspace`, so the container reuses these host-side paths directly:

- `.agents/skills`
- `.agents/mcp.json`
- `.agentseek`
- `startup.sh`

Compose uses a SQLite tape store under `/workspace/.agentseek/agentseek-tapes.db` by default.
It also auto-discovers `.agents/mcp.json` and links it into the runtime MCP config path inside the container.
To use another MCP config file, set `AGENTSEEK_MCP_CONFIG_PATH`.

## Next

- Run `uv run agentseek onboard` to collect configuration interactively.
- Use `uv run bub ...` when you want the upstream Bub CLI directly.
- See [Configuration](configuration.md) for environment variables, storage, and channel settings.
