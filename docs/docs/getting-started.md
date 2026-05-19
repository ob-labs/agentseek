# Getting Started

This tutorial gets the built-in agentseek CLI running from a fresh checkout and keeps generated runtime state inside the workspace.

You need:

- Python 3.12 or newer
- `uv`
- a model provider API key for real model responses

The commands below use `uv run agentseek ...` because they assume you are working from the repository root.

## 1. Clone And Install

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

The `agentseek` command is a Bub-compatible CLI entry point with agentseek branding and defaults.

## 2. Configure A Model

Use `AGENTSEEK_*` variables for the agentseek distribution. They are passed through to Bub as `BUB_*` aliases.

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
```

The API key above is a placeholder. Replace it with a real key before expecting model responses.

You can also copy `.env.example` to `.env` and edit the values:

```bash
cp .env.example .env
```

agentseek reads `.env` through its settings layer and maps missing `BUB_*` values from matching `AGENTSEEK_*` values.

## 3. Run A Chat Session

```bash
uv run agentseek chat
```

You should see an interactive chat session. Use `Ctrl+C` to stop it.

You can also run a single prompt through the CLI:

```bash
uv run agentseek run "Summarize this workspace in one sentence."
```

## 4. Check Local State

agentseek stores local config and runtime state under `.agentseek` in the current workspace by default.

Set `AGENTSEEK_HOME` or `BUB_HOME` to use another location.

The main defaults are:

```text
.agentseek/config.yml
.agentseek/mcp.json
.agentseek/agentseek-project
```

`agentseek install ...` uses `.agentseek/agentseek-project` as Bub's plugin sandbox unless you set `AGENTSEEK_PROJECT` or `BUB_PROJECT`.

## 5. Add Local Skills And MCP

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

```bash
export AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json
uv run agentseek chat
```

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
- optional `startup.sh`

It auto-discovers `.agents/mcp.json` and links it into the runtime MCP config path inside the container.
To use another MCP config file, set `AGENTSEEK_MCP_CONFIG_PATH`.

If the mounted workspace contains `startup.sh`, the entrypoint runs that script. Otherwise it starts:

```bash
agentseek gateway
```

Set `AGENTSEEK_DOCKER_WORKSPACE` when you want Compose to mount a different host directory into `/workspace`.

## 7. Verify The Repository

For local development, run the baseline checks:

```bash
make check
make test
make docs-test
```

## Next

- Run `uv run agentseek onboard` to collect configuration interactively into `.agentseek/config.yml`.
- Use `uv run bub ...` when you want the upstream Bub CLI directly.
- See [Configuration](configuration.md) for environment aliases, local paths, and Docker settings.
- See [Extensions](extensions.md) when you want to add project instructions, skills, MCP config, or Bub-compatible plugins.
- For contrib capabilities, use the package README files linked from [Overview](index.md).
