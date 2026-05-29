---
title: Where things live in the monorepo
type: explanation
audience: [A2, A3, A4, A5]
runs: no
verified_on: 2026-05-28
sources:
  - README.md
  - docs/index.md
  - pyproject.toml
  - contrib/agentseek-cli/pyproject.toml
  - contrib/README.md
  - examples/README.md
  - src/skills/README.md
  - skills/README.md
  - docs/hub.md
---

# Where things live in the monorepo

> **In short:** the agentseek repository is a uv workspace that ships two top-level packages:
> `agentseek` (the harness) and `agentseek-cli` (the project lifecycle CLI). Core code lives
> under `src/`, larger integrations under `contrib/`, runnable end-to-end demos under
> `examples/`, project scaffolds under `templates/`, supporting skill repos under `skills/`,
> vendored upstream code under `references/`, and the published documentation under `docs/`.

## Context

agentseek is a monorepo on purpose: the harness, the bundled plugins, the contrib
integrations, the examples, and the documentation all evolve together. The directory names
look familiar but each one has a specific role; mixing them up is the most common reason a
new contributor adds a file in the wrong place.

This page is the annotated map. For exact install commands and entry points, jump out to
the referenced READMEs rather than reading this page end-to-end.

## How it works

```text
agentseek/
├── src/
│   ├── agentseek/        ← harness package (PyPI: agentseek)
│   └── skills/           ← bundled skills shipped with the wheel
├── contrib/
│   ├── README.md         ← contrib README standard + package index
│   ├── agentseek-cli/    ← project lifecycle CLI (PyPI: agentseek-cli)
│   └── agentseek-*/      ← runtime plugin packages (workspace members)
├── examples/             ← runnable end-to-end demos
├── templates/            ← project scaffolds used by `agentseek create`
├── skills/               ← stand-alone skills, separate from `src/skills`
├── references/           ← vendored upstream sources for reading, not editing
├── docs/                 ← published documentation (Diátaxis: tutorials/how-to/reference/explanation)
├── scripts/              ← project scripts (currently empty)
├── tests/                ← top-level tests
├── entrypoint.sh         ← Docker entrypoint
├── docker-compose.yml    ← Compose definition
├── pyproject.toml        ← harness pyproject (deps, extras, workspace members)
└── README.md             ← repo README; entry point for the project
```

### `src/agentseek/` — the harness package

The Python package published to PyPI as `agentseek` (the harness itself). It is
**not** directly installable from PyPI: `requires-dist` includes `bub-feishu`,
`bub-mcp`, and `agentseek-schedule-sqlalchemy`, which are wired via
`[tool.uv.sources]` (git source / workspace). PyPI metadata cannot carry source
overrides, so a plain `pip install agentseek` or `uv tool install agentseek`
will fail to resolve. Install it by cloning this repo and running `uv sync`, or
by `uv sync`-ing inside a project generated via `agentseek create`. See
[`choosing-an-entry-point.md`](choosing-an-entry-point.md).

Three files matter:

- `src/agentseek/env.py` — alias rules from `AGENTSEEK_*` to `BUB_*` plus the location
  defaults (`.agentseek/`, `.agentseek/agentseek-project`). The mechanics are explained in
  [`bub-relationship.md`](bub-relationship.md).
- `src/agentseek/cli.py` — the three Typer monkeypatches that brand onboarding, enable
  lifecycle channels in `chat`, and re-point the install sandbox.
- `src/agentseek/__main__.py` — the boot sequence that runs the alias step, applies the CLI
  overrides, and constructs a `BubFramework`.

This is the only place core harness code lives. Everything bigger goes under `contrib/`.

### `src/skills/` — bundled skills

Skills shipped inside the distribution because `pyproject.toml:73-77` includes `src/skills`
in the build. As of this writing the directory contains `plugin-creator/`, plus skills
imported at build time from external repos via `[tool.pdm.build].skills`
(`pyproject.toml:78-80`) — currently `friendly-python` and `piglet` from
<https://github.com/PsiACE/skills>. See [`src/skills/`](https://github.com/ob-labs/agentseek/tree/main/src/skills)
for the bundled skill list and [`runtime-data-model.md`](runtime-data-model.md) for what a
skill is.

### `contrib/` — larger integrations

Workspace member packages, each a regular Python distribution with its own README. The
index and the README standard live at [`contrib/`](https://github.com/ob-labs/agentseek/tree/main/contrib).
`agentseek-cli` is a top-level PyPI package in its own right (the project
lifecycle CLI of Path A — see [`choosing-an-entry-point.md`](choosing-an-entry-point.md));
the other entries are runtime plugins for the harness.

| Directory | Role | Purpose |
| --- | --- | --- |
| `agentseek-cli` | **Project lifecycle CLI** (top-level PyPI package) | `create / run / build / deploy / api / ctx / skills`. Installable via `uv tool install agentseek-cli`; when present alongside the harness it folds into the same `agentseek` command surface. |
| `agentseek-ag-ui` | Runtime plugin | AG-UI SSE channel adapter for `agentseek gateway`. |
| `agentseek-contextseek` | Runtime plugin | ContextSeek semantic context layer. |
| `agentseek-langchain` | Runtime plugin | Routes Bub model turns through a user-supplied LangChain `Runnable`. |
| `agentseek-observability` | Runtime plugin | Logfire-backed tracing across the any-llm / Republic / Bub stack. |
| `agentseek-schedule-sqlalchemy` | Runtime plugin (bundled as a hard dep of the harness) | SQLAlchemy-backed APScheduler job store. |
| `agentseek-tapestore-oceanbase` | Runtime plugin | SQLAlchemy tape storage with OceanBase compatibility. |

Each package owns its install, configure, run, and verify documentation. The main docs
link out; they do not duplicate. The workspace mapping lives at `pyproject.toml:100-110`.

### `examples/` — runnable end-to-end demos

Outside the package source trees on purpose, so each example shows the install + run shape
of a user workspace. Today the catalogue (from [`examples/`](https://github.com/ob-labs/agentseek/tree/main/examples))
is `ag-ui`, `ag_ui_langchain`, `agentseek_api_remote_agent`, `langchain_otel_sidecar`,
`langchain_deepagents`, and `langchain_cli_remote_agent`. They are the right starting
point when you want to see the whole assembly — gateway + frontend + LangChain + agentseek
— rather than the harness alone.

### `templates/` — project scaffolds

Cookiecutter sources used by `agentseek create` (provided by `agentseek-cli`). The
catalogue lives at `templates/index.json`:

| Template | Purpose |
| --- | --- |
| `bub/default` | Lightweight Bub agent: `agentseek gateway` + CopilotKit frontend, no LangChain. |
| `langchain/default` | LangChain `create_agent` + CopilotKit middleware over `agentseek-langchain`. |
| `langchain/cli-remote` | Remote LangGraph CLI agent bridged via `LangGraphClientRunnable`. |
| `deepagents/default` | Local `create_deep_agent` runnable bound to `agentseek-langchain`. |

The directory is excluded from ty (`pyproject.toml:120-126`) and ruff
(`pyproject.toml:133-139`) because the files contain Jinja2 placeholders, not real Python.
Reference: [`../reference/templates.md`](../reference/templates.md).

### `skills/` — stand-alone skill repositories

Separate from `src/skills/`. This directory holds skills that are maintained alongside the
project but **not bundled into the `agentseek` wheel**. Today the entries are
`github-repo-cards` and `langchain-cn-models`; see
[`skills/`](https://github.com/ob-labs/agentseek/tree/main/skills) and the published
[Hub page](../hub.md) for the catalogue. Install them into your workspace under
`.agents/skills/` via `npx skills add` or by copying the folder.

### `references/` — vendored upstream sources

Read-only copies of upstream projects checked in for offline navigation and grep targets:
`agentseek-api`, `ag-ui`, `bub`, `bub-contrib`, `buildscape`, `logfire`, `republic`,
`wheels`. They are **not** dependencies. Do not edit; treat them as a search index.

### `docs/`

`docs/` holds the published documentation. The Diátaxis layout follows the four quadrants
([`../tutorials/`](../tutorials/index.md), [`../how-to/`](../how-to/index.md),
[`../reference/`](../reference/index.md), [`../explanation/`](../explanation/index.md))
plus a `blog/` archive and a published `hub.md` browse page.

Generic Diátaxis writing standards and the four page templates live in the
documentation-writer skill at `.agents/skills/documentation-writer/`. New documentation
pages go under `docs/`, following the skill's contract.

The `hub.md` page is the published browse surface for plugins, skills, and friends; it is
the source of the navigation/where-things-live picture used across the site.

### `scripts/`, `tests/`, and top-level files

- `scripts/` is reserved for project scripts and is currently empty.
- `tests/` holds top-level tests; contrib packages have their own test trees under
  `contrib/*/tests/`.
- `entrypoint.sh` and `docker-compose.yml` are the Docker entry points; see
  [`choosing-an-entry-point.md`](choosing-an-entry-point.md).
- `pyproject.toml` is the source of truth for the distribution, the optional extras, and
  the workspace member list.

## Why it is like this

- **Two packages, one workspace.** The uv workspace lets the harness
  (`agentseek`) and the project lifecycle CLI (`agentseek-cli`) ship as two
  PyPI packages while contrib plugins evolve at their own pace. Optional
  extras (`pyproject.toml:27-46`) make adopting them a one-line change inside
  the repo.
- **Bundled vs project-local skills.** Bundling skills inside the wheel makes them
  reproducible (`src/skills/`); workspace-local skills (`.agents/skills/`) make them
  hackable. Stand-alone skill repos (`skills/`) sit in between for skills that should be
  install-on-demand.
- **Examples sit outside packages.** Keeping examples in `examples/` rather than under a
  package shows the install shape teammates will actually use — extras pinned, gateway
  launched, frontend wired up.
- **References are checked in, not vendored.** They are search targets, not dependencies.
  This trade keeps grep cheap without taking on maintenance burden.

## Consequences for users

- Add core agentseek code under `src/agentseek/`. If a change needs its own dependency or
  test surface, it is a contrib package.
- New plugins go under `contrib/agentseek-<feature>/` and follow the README standard from
  [`contrib/README.md`](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md). The bundled `plugin-creator` skill
  at `src/skills/plugin-creator/` scaffolds the layout.
- New end-to-end demos go under `examples/`, not under a package.
- Skill changes go under `src/skills/` (bundled) or `.agents/skills/` (project-local);
  `skills/` is for separately-maintained stand-alone repos.
- New documentation pages go under `docs/<quadrant>/` and follow the contract in the
  `documentation-writer` skill at `.agents/skills/documentation-writer/SKILL.md`.

## Related

- How-to: [`../how-to/install-a-plugin.md`](../how-to/install-a-plugin.md),
  [`../how-to/add-skills.md`](../how-to/add-skills.md),
  [`../how-to/author-a-contrib-plugin.md`](../how-to/author-a-contrib-plugin.md)
- Reference: [`../reference/file-layout.md`](../reference/file-layout.md),
  [`../reference/packages.md`](../reference/packages.md),
  [`../reference/templates.md`](../reference/templates.md)
- Explanation: [`extension-model.md`](extension-model.md),
  [`choosing-an-entry-point.md`](choosing-an-entry-point.md)
- External: [contrib README](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md),
  [examples catalogue](https://github.com/ob-labs/agentseek/tree/main/examples),
  [Hub page](../hub.md)
