---
title: Packages reference
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-06-08
sources:
  - pyproject.toml
  - contrib/README.md
---

# Packages reference

AgentSeek ships one top-level Python package, `agentseek`. The package exposes
the public console script and the embeddable harness library.

| Field | Value | Source |
| --- | --- | --- |
| Name | `agentseek` | `pyproject.toml` |
| Version | `0.0.2` | `pyproject.toml` |
| Python | `>=3.12,<4.0` | `pyproject.toml` |
| Console script | `agentseek = "agentseek.__main__:app"` | `pyproject.toml` |
| Build backend | `pdm.backend` | `pyproject.toml` |
| Build includes | `src/agentseek`, `src/skills` | `pyproject.toml` |

## Core dependency groups

Runtime dependencies include both the harness runtime and the project command tooling:

| Package | Purpose |
| --- | --- |
| `bub` | Hook-first runtime, channels, plugins, and CLI foundation. |
| `cookiecutter` | Template rendering for `agentseek create`. |
| `jinja2` | Template rendering support. |
| `logfire` | Local instrumentation and log integration. |
| `npx-skills` | Skill CLI wrapper for `agentseek skills`. |
| `pydantic-settings` | Runtime settings. |
| `typer` | CLI construction. |

Development dependency groups remain in `pyproject.toml`:

| Group | Purpose |
| --- | --- |
| `dev` | Tests, type checks, docs, and example development. |
| `plugins` | Workspace plugin packages used while developing the monorepo. |

## Contrib packages

Contrib packages are optional extensions installed through
`agentseek plugin install <package>` or by depending on them directly from a
generated project.

| Package | Bub entry point | Workspace path |
| --- | --- | --- |
| `agentseek-ag-ui` | n/a | `contrib/agentseek-ag-ui` |
| `agentseek-langchain` | `langchain` | `contrib/agentseek-langchain` |
| `agentseek-tapestore-oceanbase` | `tapestore-oceanbase` | `contrib/agentseek-tapestore-oceanbase` |
| `agentseek-schedule-sqlalchemy` | `schedule` | `contrib/agentseek-schedule-sqlalchemy` |
| `agentseek-contextseek` | `contextseek` | `contrib/agentseek-contextseek` |

Entry points are declared by each contrib package under
`[project.entry-points.bub]`.

## uv workspace members

```text
contrib/agentseek-ag-ui
contrib/agentseek-langchain
contrib/agentseek-schedule-sqlalchemy
contrib/agentseek-tapestore-oceanbase
contrib/agentseek-contextseek
.agentseek/agentseek-project
```

The trailing `.agentseek/agentseek-project` is the default plugin sandbox.
Keeping it as a workspace member lets uv resolve locally installed plugins
against the same lockfile during development.

## Bundled skills

`[tool.pdm.build].skills` bundles these skills into the wheel:

| Source | Subpath | Skills included |
| --- | --- | --- |
| `git+https://github.com/PsiACE/skills.git` | `skills` | `friendly-python`, `piglet` |

## See also

- [CLI reference](cli.md)
- [File layout reference](file-layout.md)
- [How to install a plugin](../how-to/install-a-plugin.md)
