---
title: Packages reference
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-06-05
sources:
  - pyproject.toml
  - contrib/agentseek-cli/pyproject.toml
  - contrib/README.md
---

# Packages reference

Package layout, optional extras, contrib entry points, and uv workspace members.
All facts here mirror `pyproject.toml` at the verification date.

## Two top-level PyPI packages

agentseek ships **two complementary PyPI packages**, split by job. Both register
the same console script name `agentseek`; what `agentseek …` does depends on
which package is active in the current environment.

| Package | Role | Source | Console script | How to install |
| --- | --- | --- | --- | --- |
| `agentseek` | Harness — runtime CLI and embeddable library (`chat`, `run`, `gateway`, `install`, `update`, …) | `pyproject.toml:2`, `src/agentseek/` | `agentseek = "agentseek.__main__:app"` (`pyproject.toml:29`) | `uv tool install agentseek` for the runtime CLI; add `agentseek` as a project dependency when embedding it as a library. |
| `agentseek-cli` | Project lifecycle CLI (`create`, `run`, `build`, `deploy`, `api`, `ctx`, `skills`) | `contrib/agentseek-cli/pyproject.toml:2`, `contrib/agentseek-cli/src/agentseek_cli/` | `agentseek = "agentseek_cli.standalone:app"` (`contrib/agentseek-cli/pyproject.toml:18`) | `uv tool install agentseek-cli` (preferred), or pulled in as the `cli` extra from inside this repo |

`[tool.uv.sources]` in this repository is a development-time resolver map for
workspace and git-sourced plugin packages. It is not required for the published
`agentseek` wheel's core runtime dependencies.

### `agentseek` (harness)

| Field | Value | Source |
| --- | --- | --- |
| Name | `agentseek` | `pyproject.toml:2` |
| Version | `0.0.2` | `pyproject.toml:3` |
| Python | `>=3.12,<4.0` | `pyproject.toml:8` |
| Build backend | `pdm.backend` (`pdm-backend`, `pdm-build-skills>=0.1.0a3`) | `pyproject.toml:61` |
| Build includes | `src/agentseek`, `src/skills` | `pyproject.toml:65` |

### `agentseek-cli` (project lifecycle CLI)

| Field | Value | Source |
| --- | --- | --- |
| Name | `agentseek-cli` | `contrib/agentseek-cli/pyproject.toml:2` |
| Version | `0.0.2` | `contrib/agentseek-cli/pyproject.toml:3` |
| Python | `>=3.12` | `contrib/agentseek-cli/pyproject.toml:7` |
| Console script | `agentseek = "agentseek_cli.standalone:app"` | `contrib/agentseek-cli/pyproject.toml:18` |
| Bub entry point | `cli = "agentseek_cli.plugin:main"` | `contrib/agentseek-cli/pyproject.toml:21` |
| Build backend | `pdm.backend` | `contrib/agentseek-cli/pyproject.toml:24` |

The dual registration (`project.scripts` + `entry-points.bub`) is what lets the
same package act as a standalone CLI on Path A and a runtime plugin (folded into
`agentseek …`) on Path B. See [CLI reference](cli.md) for the command surface in
each mode.

## Harness runtime packages

These are the main runtime entries from `pyproject.toml`:

| Package | Constraint | Source pin |
| --- | --- | --- |
| `bub` | `>=0.3.7` | PyPI |
| `logfire` | `>=4.33.0` | PyPI |
| `pydantic-settings` | `>=2.0.0` | PyPI |

## Installing plugins

Plugins are installed via the `agentseek install` command. The previous
`[optional-dependencies]` extras (e.g. `pip install agentseek[langchain]`) have
been removed; only `agentseek[cli]` remains as a pip extra.

> The `cli` extra is **not the only way** to get the project lifecycle CLI;
> `uv tool install agentseek-cli` installs the same package independently.

| Plugin package | Install command | Purpose |
| --- | --- | --- |
| `agentseek-ag-ui` | `agentseek install agentseek-ag-ui` | AG-UI adapter and FastAPI helpers. |
| `agentseek-cli` | `agentseek install agentseek-cli` or `uv tool install agentseek-cli` | Project lifecycle CLI folded into the harness env (`create / run / build / deploy / api / ctx / skills`). |
| `agentseek-langchain` | `agentseek install agentseek-langchain` | LangChain `Runnable` / agent bridge. |
| `bub-tapestore-otel` | `agentseek install bub-tapestore-otel@main` | Tape-first OpenTelemetry spans exported through OTLP HTTP. |
| `agentseek-tapestore-oceanbase` | `agentseek install agentseek-tapestore-oceanbase` | SQLAlchemy tape storage with OceanBase compatibility. |
| `agentseek-contextseek` | `agentseek install agentseek-contextseek` | ContextSeek semantic context runtime plugin (also brings the lifecycle CLI for `agentseek ctx`). |

## Contrib packages

Workspace members live under `contrib/` (`pyproject.toml:92`). Each owns its
own README; do not duplicate config here.

`agentseek-cli` is listed in this table for completeness, but it is a top-level
PyPI package in its own right (see the table at the top of this page), not a
runtime plugin like the others.

| Package | Bub entry point | Workspace path | README |
| --- | --- | --- | --- |
| `agentseek-cli` (project lifecycle CLI) | `cli` | `contrib/agentseek-cli` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-cli/README.md) |
| `agentseek-ag-ui` | n/a | `contrib/agentseek-ag-ui` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-ag-ui/README.md) |
| `agentseek-langchain` | `langchain` | `contrib/agentseek-langchain` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-langchain/README.md) |
| `agentseek-tapestore-oceanbase` | `tapestore-oceanbase` | `contrib/agentseek-tapestore-oceanbase` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-tapestore-oceanbase/README.md) |
| `agentseek-schedule-sqlalchemy` | `schedule` | `contrib/agentseek-schedule-sqlalchemy` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-schedule-sqlalchemy/README.md) |
| `agentseek-contextseek` | `contextseek` | `contrib/agentseek-contextseek` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md) |

Entry points are declared by each contrib package under
`[project.entry-points.bub]`. The Bub entry point column reproduces
`contrib/README.md`.

## uv workspace members

```text
contrib/agentseek-ag-ui
contrib/agentseek-cli
contrib/agentseek-langchain
contrib/agentseek-schedule-sqlalchemy
contrib/agentseek-tapestore-oceanbase
contrib/agentseek-contextseek
.agentseek/agentseek-project
```

The trailing `.agentseek/agentseek-project` is the **default plugin sandbox**;
including it as a workspace member allows uv to resolve plugins installed by
`agentseek install` against the same lockfile (`pyproject.toml:100`).

## Skills bundled at build time

`[tool.pdm.build].skills` (`pyproject.toml:70`):

| Source | Subpath | Skills included |
| --- | --- | --- |
| `git+https://github.com/PsiACE/skills.git` | `skills` | `friendly-python`, `piglet` |

These ship inside the wheel under the top-level `skills/` package, alongside
the project's own `src/skills/` contents.

## Index URL

`[tool.uv]` pins `index-url = "https://pypi.org/simple"`
(`pyproject.toml:76`). For faster dev installs, set `UV_INDEX_URL` to a
mirror (e.g. `https://pypi.tuna.tsinghua.edu.cn/simple`).

## See also

- Overview: [agentseek](../index.md)
- Explanation: [Choosing an entry point](../explanation/choosing-an-entry-point.md)
- How-to: [How to install a plugin](../how-to/install-a-plugin.md),
  [How to author a contrib plugin](../how-to/author-a-contrib-plugin.md)
- Reference: [CLI reference](cli.md), [File layout reference](file-layout.md)
