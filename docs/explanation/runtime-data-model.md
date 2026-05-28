---
title: The runtime data model
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-05-28
sources:
  - src/agentseek/__main__.py
  - src/agentseek/cli.py
  - pyproject.toml
  - contrib/README.md
  - blog/introducing-agentseek.md
---

# The runtime data model

> **In short:** five things flow through the harness — **tapes**, **skills**, **MCP**
> servers, **plugins**, and **channels**. The first is the durable substrate; the others
> shape what enters and leaves a turn. Understanding which is which makes the extension
> model in [`extension-model.md`](extension-model.md) obvious.

## Context

agentseek packages Bub, and Bub is small on purpose: a kernel that runs turns and a plugin
system that supplies everything else (see
[Why we rewrote Bub](https://bub.build/posts/why-rewrite-bub/)). The five concepts below
are Bub's vocabulary; agentseek inherits them unchanged and adds defaults for where they
live in a workspace.

If you have only used the CLI, this page is the bridge between "I sent a chat message" and
"I want to plug my application into this runtime."

## How it works

```text
                  ┌──────────────────────────────────────────┐
   user / app ──► │  channel  (cli, gateway, feishu, ag-ui…) │
                  └───────────────────┬──────────────────────┘
                                      │  turn
                  ┌───────────────────▼──────────────────────┐
                  │           framework (Bub kernel)         │
   plugins ─────► │   hooks: provide_tape_store, model,      │
                  │          tools, schedule, channels…      │
                  └──────┬─────────────┬─────────────┬───────┘
                         │             │             │
                  ┌──────▼───┐  ┌──────▼───┐  ┌──────▼──────┐
                  │  skills  │  │   MCP    │  │   tape      │
                  │ (advice) │  │ (tools)  │  │ (durable)   │
                  └──────────┘  └──────────┘  └─────────────┘
```

### Tapes — the durable substrate

A **tape** is an append-only stream of facts about a turn: the input message, the model
calls, the tool calls and their results, anchors, and any derived views. The model is
described in [Tape Systems](https://tape.systems/); agentseek treats it as the canonical
runtime data shape, which is what "database-native" means in practice (see
[`../blog/introducing-agentseek.md`](../blog/introducing-agentseek.md)).

Bub exposes persistence through the `provide_tape_store` hook. Plugins that implement that
hook decide where tape entries land:

- The default Bub tape store writes to a local SQLite file inside `BUB_HOME` (which is
  `.agentseek/` under agentseek defaults — see [`bub-relationship.md`](bub-relationship.md)
  for how that default is set).
- `agentseek-tapestore-oceanbase` swaps in SQLAlchemy storage with OceanBase compatibility
  and optional vector retrieval. The full configuration lives in its own README
  ([`contrib/agentseek-tapestore-oceanbase/`](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-tapestore-oceanbase)).

Because the tape captures input + steps + output as one stream, the same data feeds
debugging, replay, trajectory comparison, evaluation, and training without copying through
side channels.

### Skills — task-specific behaviour

A **skill** is a small Markdown bundle (one folder containing a `SKILL.md`) that teaches an
agent how to do one task. Bub discovers skills from the workspace and from packages. In
this repository:

- **Project-local skills** live at `.agents/skills/<skill-name>/SKILL.md`. They take effect
  during local runs because Bub discovers them from the workspace; the Docker entrypoint
  preserves the same path inside the container (`entrypoint.sh:7-8,30-35`).
- **Bundled skills** live under `src/skills/<skill-name>/SKILL.md` and ship inside the
  `agentseek` distribution because `pyproject.toml:73-77` includes `src/skills` in the
  build.
- **External skills** can be imported at build time through `[tool.pdm.build].skills`
  (`pyproject.toml:78-80`), which is how `friendly-python` and `piglet` are bundled today.

Skills are advisory: they shape what the model does, but they do not register new tools or
hooks. When a change *is* runtime behaviour — a new model provider, a new channel, a tape
store, a tool integration — write a plugin instead. The decision matrix is in
[`extension-model.md`](extension-model.md).

### MCP — external tools, declared in config

The **Model Context Protocol** is the standard way for the agent to call tools that live
outside the Python process. Bub's `bub-mcp` plugin (a hard dependency of agentseek,
`pyproject.toml:21`) reads an MCP config file and exposes each declared server as a tool
set the model can invoke.

The default path comes from the alias layer:

- `bub-mcp` reads `${BUB_HOME}/mcp.json` by default, which is `.agentseek/mcp.json` under
  agentseek defaults.
- You can move the file to the project root by setting
  `AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json`. Inside containers the entrypoint
  auto-discovers `.agents/mcp.json` and links it into the runtime path
  (`entrypoint.sh:11-15, 37-39`).

MCP servers are good for tool integrations that should be **declared, not coded** — issue
trackers, search backends, internal services. When the tool integration needs lifecycle
behaviour or its own hooks, reach for a plugin.

### Plugins — the runtime extension surface

A **plugin** is a Python package that registers itself through the `[project.entry-points.bub]`
group and supplies one or more hook implementations. Plugins are how Bub gets channels,
model providers, tape stores, schedulers, and tool packages.

agentseek ships a few plugins as hard dependencies (`pyproject.toml:19-25`) — Bub itself,
`bub-feishu`, `bub-mcp`, `agentseek-schedule-sqlalchemy`, plus `logfire` for telemetry —
and exposes the rest as optional extras (`pyproject.toml:27-46`):

| Extra | Adds | Source |
| --- | --- | --- |
| `ag-ui` | `agentseek-ag-ui` AG-UI channel adapter | `pyproject.toml:28-30` |
| `cli` | `agentseek-cli` project-lifecycle commands | `pyproject.toml:31-33` |
| `langchain` | `agentseek-langchain` model routing | `pyproject.toml:34-36` |
| `observability` | `agentseek-observability` Logfire tracing | `pyproject.toml:37-39` |
| `oceanbase` | `agentseek-tapestore-oceanbase` tape storage | `pyproject.toml:40-42` |
| `context` | `agentseek-cli` + `agentseek-contextseek` | `pyproject.toml:43-46` |

Plugins are installed into the **same Python environment** as agentseek; they are not
sandboxed runtime units. The `agentseek install` sandbox at `.agentseek/agentseek-project`
(see [`bub-relationship.md`](bub-relationship.md)) is a uv project used to resolve and add
plugins, not a runtime boundary.

### Channels — how a turn enters and leaves

A **channel** is the surface that takes a message in and streams a response out. CLI
(`cli`) is one; the gateway / HTTP transport is another; chat platforms like Feishu and
Telegram are channels supplied by plugins (`bub-feishu` is a hard dependency,
`pyproject.toml:20`). The `agentseek-ag-ui` plugin adds an AG-UI SSE channel adapter for
front-ends like CopilotKit.

agentseek's CLI override enables **all `*.lifecycle` channels** alongside whichever primary
channel you asked for (`src/agentseek/cli.py:51-57, 83-112`). That is the mechanism that
lets MCP and other helpers boot inside an interactive `agentseek chat` session — they
register themselves on a lifecycle channel and the manager wakes them up before the first
turn.

## Why it is like this

- **One substrate, many consumers.** Putting tapes at the centre means debugging, replay,
  evaluation, and training all read from the same place; new consumers do not require new
  pipelines. That is the wager described in
  [`../blog/introducing-agentseek.md`](../blog/introducing-agentseek.md).
- **Small kernel, many plugins.** Bub keeps the kernel small so the failure surface stays
  small; everything else is a plugin you can swap, version, or remove. agentseek inherits
  that shape rather than baking storage and channels into the distribution itself.
- **Skills above the model, MCP and plugins around it.** Skills shape what the model says;
  MCP and plugins shape what it can do. Keeping the two surfaces separate keeps authoring
  cheap (drop a Markdown file) and runtime extension deliberate (ship a Python package).

## Consequences for users

- If you want to **read or query runtime data**, target the tape store. Pick a backend
  through the `provide_tape_store` plugin; do not invent a sidecar log.
- If you want to **change how the model reasons about a task**, write a skill.
- If you want to **add a tool the model can call** that already speaks MCP, declare it in
  the MCP config; otherwise write a plugin.
- If you want a **new place the agent can be reached from**, write or install a channel
  plugin.
- Hard dependencies (Bub, `bub-feishu`, `bub-mcp`, `agentseek-schedule-sqlalchemy`) are
  always present in any agentseek install; everything else is opt-in.

## Related

- Tutorial: [`../tutorials/03-add-a-skill-and-mcp.md`](../tutorials/03-add-a-skill-and-mcp.md)
- How-to: [`../how-to/add-skills.md`](../how-to/add-skills.md),
  [`../how-to/add-mcp-server.md`](../how-to/add-mcp-server.md),
  [`../how-to/install-a-plugin.md`](../how-to/install-a-plugin.md)
- Reference: [`../reference/packages.md`](../reference/packages.md),
  [`../reference/file-layout.md`](../reference/file-layout.md)
- Explanation: [`extension-model.md`](extension-model.md),
  [`bub-relationship.md`](bub-relationship.md)
- External: [Tape Systems](https://tape.systems/),
  [Why we rewrote Bub](https://bub.build/posts/why-rewrite-bub/),
  [Model Context Protocol](https://modelcontextprotocol.io/)
