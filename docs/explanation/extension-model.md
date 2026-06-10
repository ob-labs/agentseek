---
title: The extension model
type: explanation
audience: [A2, A3, A5]
runs: no
verified_on: 2026-05-28
sources:
  - docs/how-to/install-a-plugin.md
  - AGENTS.md
  - contrib/README.md
  - pyproject.toml
  - src/agentseek/cli/runtime.py
---

# The extension model

> **In short:** every change you might want to make to an agentseek runtime maps to one of
> five places — **project instructions**, **skills**, **plugins**, **MCP servers**, or
> **contrib packages**. Pick the smallest one that fits, and let the others stay empty.

## Context

People rarely extend an agent in only one way. They want to teach it a fact, give it a
tool, swap out the model provider, hand it a new transport, persist its state somewhere
else, and ship a maintained integration to teammates — all on the same project. Without a
clear matrix, every change tends to default to "write a plugin", which over-builds simple
cases, or "edit prompts", which underserves runtime needs.

agentseek inherits Bub's extension surfaces unchanged. This page is the decision matrix
that lets you choose between them before you open the matching how-to.

## How it works

### The matrix

Use the smallest extension point that matches the change. This is the same rule that
historically opened the old `extensions.md`, promoted to a pure explanation page so the
how-tos can stay short.

| Need | Use | Authoring shape | Lives at | When to grow out of it |
| --- | --- | --- | --- | --- |
| Durable project instructions (channels, conventions, runtime rules) | **Project instructions** | One Markdown file | [AGENTS.md](https://github.com/ob-labs/agentseek/blob/main/AGENTS.md) | When the rule depends on runtime state or a specific tool call — that is a skill or plugin. |
| Task-specific behaviour, workflow knowledge, small script the agent should know how to call | **Agent Skill** | `SKILL.md` (+ optional scripts) in a folder | `.agents/skills/` (project), `src/skills/` (bundled) | When you need a new hook, channel, store, or tool registration. |
| Runtime hooks, channels, tools, stores, schedulers, model providers | **Bub-compatible plugin** | Python package with `[project.entry-points.bub]` | Installed into the same venv as agentseek; sandbox at `.agentseek/agentseek-project` | When the integration is large enough to own docs, tests, and optional deps — that is a contrib package. |
| External tool or service that already speaks MCP | **MCP server entry** | JSON entry in `mcp.json` | `.agentseek/mcp.json` (default) or `.agents/mcp.json` | When the integration needs runtime hooks of its own — write a plugin. |
| Larger maintained integration with its own deps, config, examples | **Contrib package** | Python package under `contrib/agentseek-*/` | Monorepo workspace member; opt-in extra in `pyproject.toml:27-46` | This is the terminal step; contrib packages own their own docs. |

### Why one row, not many

If you can solve the change with **project instructions**, do that and stop. If a fact
needs *behaviour* — call this script, follow this workflow — promote it to a **skill**. If
that workflow needs the runtime to know about something new — a new channel, a tape store,
a tool the model can call directly — promote it to a **plugin**. If the runtime change is
"the model should reach an external server I do not own", an **MCP entry** is the cheaper
form. Anything that comes with its own deps, config sections, and tests becomes a **contrib
package**, which is just a plugin with a README contract.

The five rows are deliberately ordered by cost. The rest of the docs reinforce that
ordering: how-tos lead with the cheapest form, reference pages list the exact knobs, and
the contrib monorepo (`contrib/README.md`) sets the standard for the heaviest step.

### Bub conventions the matrix relies on

- Plugins register through `[project.entry-points.bub]` (`contrib/README.md`).
- Skills are discovered from the workspace (`.agents/skills/`) and from packaged
  distributions (bundled `src/skills` is included in the build via
  `pyproject.toml:73-77`).
- The MCP config path follows the alias model from
  [How agentseek relates to Bub](bub-relationship.md): `${BUB_HOME}/mcp.json` by default, override
  via `AGENTSEEK_MCP_CONFIG_PATH`.
- The install sandbox at `.agentseek/agentseek-project` is created on demand by
  `src/agentseek/cli/runtime.py:115-140`. Plugins land in that sandbox's environment, not in a
  runtime-isolated unit.

## Why it is like this

- **Cheap things should stay cheap.** A new fact should not need a Python package; a
  workflow should not need a plugin. The matrix exists so that the right answer is usually
  also the smallest.
- **Runtime extension is deliberate, not accidental.** Hooks, channels, and stores all
  affect every turn. Putting them behind a packaging step (a plugin or a contrib package)
  makes the choice visible and reviewable.
- **Contrib README is the doc standard.** Once an integration is heavy enough to need
  install steps, env vars, and runtime behaviour notes, those facts belong next to the
  code. That is why [contrib/README.md](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md) defines a fixed
  section order and the main docs only link out.
- **`AGENTSEEK_*` environment variables** are the preferred prefix for distribution-scoped
  settings. See [Environment reference](../reference/environment.md) for details.

## How to decide

- The first question to ask is "where on the matrix does this belong?" — not "do I need a
  plugin?".
- Project instructions in [AGENTS.md](https://github.com/ob-labs/agentseek/blob/main/AGENTS.md) apply to every turn in this
  repo; treat them as durable, not as scratch space.
- Anything that would otherwise become a `print` statement in your own code probably
  belongs in a skill or a plugin hook; the tape captures it in either case.
- Heavy integrations that you maintain for others should land under
  `contrib/agentseek-<feature>/` and follow the README standard from the start. The
  `plugin-creator` bundled skill at `src/skills/plugin-creator/` scaffolds the layout.
- The matrix is also the navigation key for the how-to group: each row has a how-to page
  (and, for skills and MCP, a reference page) you can jump to once the row is picked.

## Related

- How-to:
  - Project instructions: edit [AGENTS.md](https://github.com/ob-labs/agentseek/blob/main/AGENTS.md) directly.
  - [How to add skills](../how-to/add-skills.md)
  - [How to install a plugin](../how-to/install-a-plugin.md)
  - [How to add an MCP server](../how-to/add-mcp-server.md)
  - [How to author a contrib plugin](../how-to/author-a-contrib-plugin.md)
- Reference: [Packages reference](../reference/packages.md),
  [File layout reference](../reference/file-layout.md)
- Explanation: [The runtime data model](runtime-data-model.md),
  [How agentseek relates to Bub](bub-relationship.md)
- External: [Bub Hub](https://hub.bub.build),
  [Model Context Protocol](https://modelcontextprotocol.io/)
