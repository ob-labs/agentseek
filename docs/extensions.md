# Extensions

This guide explains the supported extension points for agentseek projects. For runtime settings, see [Configuration](configuration.md).

agentseek follows Bub's extension model. The agentseek layer adds naming conventions, environment aliases, packaging defaults, and bundled skills; it does not replace Bub hooks or entry points.

## Project Instructions

Use `AGENTS.md` to teach agents how to operate in your project.

Good project instructions usually include:

- which channels are enabled, such as `$feishu` or `$telegram`
- when the agent should reply directly and when it should call a channel-specific send tool
- repository-specific coding, testing, and documentation rules
- runtime constraints that should be followed on every task

Keep `AGENTS.md` focused on durable behavior. Do not put credentials, deployment-only secrets, or one-off task notes in it.

## Extend With Plugins

Plugins add runtime behavior through Bub's hook system. Use this path when you need a new channel, model provider, store, tool package, scheduler, or other runtime integration.

### Install A Plugin

Plugins install into the **same Python environment** as agentseek. Browse the ecosystem on [Bub Hub](https://hub.bub.build/): it lists plugins with install specs such as `bub install bub-feishu@main`.

#### From Bub Hub

Hub entries typically use `bub install …`. The agentseek CLI exposes the same resolver:

```bash
agentseek install bub-feishu@main
```

`install` accepts package specs described in its help output: a git URL, `owner/repo`, or a package name **published through the Bub contrib resolver** (often `name@branch`). It is **not** a generic PyPI installer for arbitrary distribution names.

By default, agentseek sets `BUB_PROJECT` to `{BUB_HOME}/agentseek-project` (so `AGENTSEEK_PROJECT` can override it). New sandboxes use `uv init --name agentseek-project` instead of `bub-project`.

Use `bub install …` instead if you prefer the upstream Bub entry point; behavior matches the Hub examples.

#### Path, Extra, Or Git For agentseek Contrib Packages

Packages that live only in this repository (for example `agentseek-schedule-sqlalchemy` under `contrib/`) are **not** guaranteed to resolve when you run `agentseek install agentseek-schedule-sqlalchemy` or `uv add agentseek-schedule-sqlalchemy` outside the monorepo. Prefer wiring them explicitly:

```bash
uv add ./contrib/agentseek-schedule-sqlalchemy
```

For contrib packages that are also exposed as root extras in this monorepo, prefer the extra when you are working from the repository root. Do not `uv add ./contrib/...` for those packages from the root workspace:

```bash
uv sync --extra langchain
uv sync --extra oceanbase
```

For packages without a root extra, or when you want the plugin package by itself, use a path or Git install. For example:

```bash
uv pip install "git+https://github.com/ob-labs/agentseek.git#subdirectory=contrib/agentseek-schedule-sqlalchemy"
```

When you vendor the package next to your project, the dependency entry looks like:

```toml
[project]
dependencies = [
    "agentseek-schedule-sqlalchemy",
]
```

For workspace packages, also wire the source:

```toml
[tool.uv.sources]
agentseek-schedule-sqlalchemy = { workspace = true }

[tool.uv.workspace]
members = [
    "contrib/agentseek-schedule-sqlalchemy",
]
```

The package must expose a Bub entry point:

```toml
[project.entry-points.bub]
schedule = "agentseek_schedule_sqlalchemy.plugin:main"
```

After changing dependencies, refresh the environment:

```bash
uv lock
uv sync
```

### Create A Plugin

Create an agentseek-owned plugin under `contrib/agentseek-<feature>/` unless the user asks for another location.

Use these conventions:

- distribution name: `agentseek-<feature>`
- Python package: `agentseek_<feature>`
- entry point group: `[project.entry-points.bub]`
- environment variables: prefer `AGENTSEEK_*`, accept `BUB_*` when the setting maps to Bub runtime behavior

When both prefixes are supported for the same setting, `BUB_*` should take precedence. This keeps the plugin usable from plain Bub while letting agentseek projects document `AGENTSEEK_*` names.

agentseek bundles an agentseek-adapted `plugin-creator` skill to help scaffold or update Bub-compatible plugin packages according to these conventions. It follows the upstream Bub contrib workflow shape, but specializes the guidance for `contrib/agentseek-*`, bundled `src/skills`, and `AGENTSEEK_*` alias behavior in this repository.

## Extend With Skills

Skills teach agents task-specific behavior. Use this path when the extension is instruction, workflow knowledge, or a small script the agent should know how to call. Use a plugin instead when the runtime itself needs a new hook, channel, store, or tool registration.

### Install Skills In A Project

Install project-local skills under:

```text
.agents/skills/<skill-name>/SKILL.md
```

Install skills from a registry into `.agents/skills` using `npx skills add`, matching [Bub Hub](https://hub.bub.build/) examples:

```bash
npx skills add psiace/skills --skill friendly-python
npx skills add bubbuild/bub-contrib --skill plugin-creator
```

This is the right place for repository-specific workflows that should not ship with the agentseek package.

This path works for local `agentseek` runs immediately because Bub discovers project skills from the workspace.

In containers or compose, the entrypoint preserves the same `.agents/skills` convention by default, so host-installed skills can be reused directly.

## Extend With MCP

If you want to attach MCP servers to the runtime, `bub-mcp` reads MCP config from `${BUB_HOME}/mcp.json` by default. With agentseek defaults, the local path is:

```text
.agentseek/mcp.json
```

If you prefer to keep the MCP file in the project root instead, this also works without Docker:

```bash
export AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json
uv run agentseek chat
```

In Docker / Compose, the entrypoint adds one convenience behavior: it auto-discovers `.agents/mcp.json` from the mounted workspace and links it into the runtime MCP config path. If you need another path, set `AGENTSEEK_MCP_CONFIG_PATH` or `BUB_MCP_CONFIG_PATH` explicitly.

### Bundle Skills With agentseek

Bundle release skills under:

```text
src/skills/<skill-name>/SKILL.md
```

Bundled skills are included in the agentseek package because `src/skills` is part of the build includes.

Use bundled skills for behavior that should be available wherever agentseek is installed. Keep them stable, general, and aligned with the agentseek extension model.

### Use External Skill Sources

The build can also import selected skills from external repositories through `[tool.pdm.build].skills`.

Use this for shared upstream skills. Prefer bundling under `src/skills` when the skill is agentseek-specific or has been adapted to agentseek conventions.
