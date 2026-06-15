---
title: Packages reference
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-06-15
sources:
  - pyproject.toml
  - contrib/README.md
---

# Packages reference

## Distribution

| Field | Value |
| --- | --- |
| Package name | `agentseek` |
| Version | `0.0.3` |
| Python | `>=3.12,<3.14` |
| Console script | `agentseek = "agentseek.__main__:app"` |
| Build backend | `pdm.backend` |
| Build includes | `src/agentseek`, `src/skills` |

## Runtime dependencies

| Package | Purpose |
| --- | --- |
| `bub` | Runtime kernel, channels, plugins, and CLI foundation. |
| `cookiecutter` | Template rendering for `agentseek create`. |
| `jinja2` | Template rendering support. |
| `logfire` | Instrumentation and logging integration. |
| `npx-skills` | Skill CLI wrapper for `agentseek skills`. |
| `pydantic-settings` | Runtime settings. |
| `typer` | CLI construction. |

## Dependency groups

| Group | Contents |
| --- | --- |
| `dev` | Tests, type checks, docs, and example development. |
| `plugins` | Plugin packages used while developing the workspace. |

## Package boundaries

| Boundary | Meaning |
| --- | --- |
| Core package | `agentseek` provides the console script, project commands, runtime defaults, and bundled skills. |
| Contrib package | Optional integration package with its own dependencies, tests, README, and Bub entry point. |
| Plugin environment | `.agentseek/agentseek-project` is the uv project used for plugin dependency resolution. It is not a runtime sandbox boundary. |

## Plugin group packages

| Package |
| --- |
| `bub-feishu` |
| `bub-mcp` |
| `bub-tapestore-otel` |
| `agentseek-schedule-sqlalchemy` |
| `agentseek-ag-ui` |
| `agentseek-langchain` |
| `agentseek-tapestore-oceanbase` |
| `agentseek-contextseek` |

## Contrib packages

| Package | Bub entry point | Workspace path |
| --- | --- | --- |
| `agentseek-ag-ui` | `ag-ui` | `contrib/agentseek-ag-ui` |
| `agentseek-langchain` | `langchain` | `contrib/agentseek-langchain` |
| `agentseek-tapestore-oceanbase` | `tapestore-oceanbase` | `contrib/agentseek-tapestore-oceanbase` |
| `agentseek-schedule-sqlalchemy` | `schedule` | `contrib/agentseek-schedule-sqlalchemy` |
| `agentseek-contextseek` | `contextseek` | `contrib/agentseek-contextseek` |

## uv workspace members

| Path |
| --- |
| `contrib/agentseek-ag-ui` |
| `contrib/agentseek-langchain` |
| `contrib/agentseek-schedule-sqlalchemy` |
| `contrib/agentseek-tapestore-oceanbase` |
| `contrib/agentseek-contextseek` |
| `.agentseek/agentseek-project` |

## Bundled skills

| Source | Subpath | Included skills |
| --- | --- | --- |
| `git+https://github.com/PsiACE/skills.git` | `skills` | `friendly-python`, `piglet` |
