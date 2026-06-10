---
title: Where things live in the monorepo
type: explanation
audience: [A2, A3, A4, A5]
runs: no
verified_on: 2026-06-08
sources:
  - README.md
  - pyproject.toml
  - contrib/README.md
---

# Where things live in the monorepo

AgentSeek is a uv workspace. Core package code lives under `src/`, optional
integrations under `contrib/`, project templates under `templates/`, runnable
examples under `examples/`, and documentation under `docs/`.

```text
agentseek/
├── src/
│   ├── agentseek/        ← main package: runtime, CLI, project commands
│   └── skills/           ← skills bundled into the wheel
├── contrib/              ← optional runtime integration packages
├── examples/             ← runnable end-to-end demos
├── templates/            ← Cookiecutter sources for `agentseek create`
├── skills/               ← standalone skills maintained beside the project
├── references/           ← upstream source snapshots for reading
├── docs/                 ← published documentation
├── tests/                ← top-level tests
├── entrypoint.sh         ← Docker entrypoint
├── docker-compose.yml    ← Compose definition
└── pyproject.toml        ← package, dependency, and workspace source of truth
```

## `src/agentseek`

The published `agentseek` package. It contains:

- runtime defaults and `AGENTSEEK_*` aliases;
- CLI normalization over Bub commands;
- project commands in `src/agentseek/cli`;
- the public `agentseek` console entry point.

## `contrib`

Optional packages that extend the runtime through Bub entry points or provide
framework/storage integrations. Each package owns its README, tests, and
configuration reference.

## `templates`

Cookiecutter sources used by `agentseek create`. Templates can generate Bub,
LangChain, or DeepAgents projects, and may depend on AgentSeek or remain
self-contained depending on their purpose.

## `skills`

`src/skills` contains skills bundled with the wheel. Top-level `skills/`
contains standalone skills maintained beside the project.

## `references`

Read-only upstream source snapshots used for local inspection. They are search
targets, not dependencies.

## Rule of thumb

### `examples/` — runnable end-to-end demos

Outside the package source trees on purpose, so each example shows the install + run shape
of a user workspace. Today the catalogue (from [examples/](https://github.com/ob-labs/agentseek/tree/main/examples))
is `agentseek_api_remote_agent` and `langchain_otel_sidecar`. They are the right starting
point when you want to see the whole assembly — gateway + frontend + LangChain + agentseek
— rather than the harness alone. Other common patterns (AG-UI, LangChain default, CLI
remote, DeepAgents) are covered by the `agentseek create` templates.

### `templates/` — project scaffolds

Cookiecutter sources used by `agentseek create`. The catalogue lives at
`templates/index.json`:

| Template | Purpose |
| --- | --- |
| `bub/default` | Lightweight Bub agent: `agentseek gateway` + CopilotKit frontend, no LangChain. |
| `langchain/default` | LangChain `create_agent` + CopilotKit middleware over `agentseek-langchain`. |
| `langchain/cli-remote` | Remote LangGraph CLI agent bridged via `LangGraphClientRunnable`. |
| `deepagents/default` | Local `create_deep_agent` runnable bound to `agentseek-langchain`. |

The directory is excluded from ty (`pyproject.toml:111-117`) and ruff
(`pyproject.toml:124-130`) because the files contain Jinja2 placeholders, not real Python.
Reference: [Templates reference](../reference/templates.md).

### `skills/` — stand-alone skill repositories

Separate from `src/skills/`. This directory holds skills that are maintained alongside the
project but **not bundled into the `agentseek` wheel**. Today the entries are
`github-repo-cards` and `langchain-cn-models`; see
[skills/](https://github.com/ob-labs/agentseek/tree/main/skills) and the published
[Hub page](../hub.md) for the catalogue. Install them into your workspace under
`.agents/skills/` via `npx skills add` or by copying the folder.

### `references/` — vendored upstream sources

Read-only copies of upstream projects checked in for offline navigation and grep targets:
`agentseek-api`, `ag-ui`, `bub`, `bub-contrib`, `buildscape`, `logfire`, `republic`,
`wheels`. They are **not** dependencies. Do not edit; treat them as a search index.

### `docs/`

`docs/` holds the published documentation. The Diátaxis layout follows the four quadrants
([Tutorials](../tutorials/index.md), [How-to index](../how-to/index.md),
[Reference index](../reference/index.md), [Explanation — understanding agentseek](../explanation/index.md))
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
  [Command overview](cli-surface.md).
- `pyproject.toml` is the source of truth for the distribution, the dependencies, and
  the workspace member list.

## Why it is like this

- **One package, one CLI.** The published harness package (`agentseek`) owns
  the runtime, the public CLI entry point, and project commands. Contrib
  plugins still evolve at their own pace and are installed via
  `agentseek plugin install <package>`.
- **Bundled vs project-local skills.** Bundling skills inside the wheel makes them
  reproducible (`src/skills/`); workspace-local skills (`.agents/skills/`) make them
  hackable. Stand-alone skill repos (`skills/`) sit in between for skills that should be
  install-on-demand.
- **Examples sit outside packages.** Keeping examples in `examples/` rather than under a
  package shows the install shape teammates will actually use — plugins installed, gateway
  launched, frontend wired up.
- **References are checked in, not vendored.** They are search targets, not dependencies.
  This trade keeps grep cheap without taking on maintenance burden.

## Where to put your code

- Add core agentseek code under `src/agentseek/`. If a change needs its own dependency or
  test surface, it is a contrib package.
- New plugins go under `contrib/agentseek-<feature>/` and follow the README standard from
  [contrib/README.md](https://github.com/ob-labs/agentseek/blob/main/contrib/README.md). The bundled `plugin-creator` skill
  at `src/skills/plugin-creator/` scaffolds the layout.
- New end-to-end demos go under `examples/`, not under a package.
- Skill changes go under `src/skills/` (bundled) or `.agents/skills/` (project-local);
  `skills/` is for separately-maintained stand-alone repos.
- New documentation pages go under `docs/<quadrant>/` and follow the contract in the
  `documentation-writer` skill at `.agents/skills/documentation-writer/SKILL.md`.

## Related

- [Packages reference](../reference/packages.md)
- [File layout reference](../reference/file-layout.md)
- [Command overview](cli-surface.md)
