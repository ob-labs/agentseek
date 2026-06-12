---
title: Packages reference
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-06-12
sources:
  - pyproject.toml
  - contrib/README.md
---

# Packages reference

## Distribution

| Field | Value |
| --- | --- |
| Package name | `agentseek` |
| Version | `0.0.2` |
| Python | `>=3.12,<4.0` |
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
