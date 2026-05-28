---
title: Packages reference
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-05-28
sources:
  - pyproject.toml
  - contrib/README.md
---

# Packages reference

Distribution layout, optional extras, contrib entry points, and uv workspace
members. All facts here mirror `pyproject.toml` at the verification date.

## Distribution

| Field | Value | Source |
| --- | --- | --- |
| Name | `agentseek` | `pyproject.toml:2` |
| Version | `0.1.0` | `pyproject.toml:3` |
| Python | `>=3.12,<4.0` | `pyproject.toml:8` |
| Console script | `agentseek = "agentseek.__main__:app"` | `pyproject.toml:49` |
| Build backend | `pdm.backend` (`pdm-backend`, `pdm-build-skills>=0.1.0a3`) | `pyproject.toml:69` |
| Build includes | `src/agentseek`, `src/skills` | `pyproject.toml:74` |

## Core dependencies

| Package | Constraint | Source pin |
| --- | --- | --- |
| `bub` | `>=0.3.7` | PyPI |
| `bub-feishu` | (no version) | `git+bub-contrib@5374c8f` (`pyproject.toml:89`) |
| `bub-mcp` | (no version) | `git+bub-contrib@5374c8f` (`pyproject.toml:90`) |
| `agentseek-schedule-sqlalchemy` | (no version) | workspace |
| `logfire` | `>=4.33.0` | PyPI |
| `pydantic-settings` | `>=2.0.0` | PyPI |

## Optional extras

Defined in `pyproject.toml:27`. Install with `uv pip install
'agentseek[<extra>]'` or `uv sync --extra <extra>`.

| Extra | Pulls in | Purpose |
| --- | --- | --- |
| `ag-ui` | `agentseek-ag-ui` | AG-UI adapter and FastAPI helpers. |
| `cli` | `agentseek-cli` | Project-lifecycle CLI (`create / run / build / deploy / api / ctx / skills`). |
| `langchain` | `agentseek-langchain` | LangChain `Runnable` / agent bridge. |
| `observability` | `agentseek-observability` | Logfire-backed spans. |
| `oceanbase` | `agentseek-tapestore-oceanbase` | SQLAlchemy tape storage with OceanBase compatibility. |
| `context` | `agentseek-cli`, `agentseek-contextseek` | ContextSeek semantic context runtime plugin (also brings the CLI for `agentseek ctx`). |

## Contrib packages

Workspace members live under `contrib/` (`pyproject.toml:101`). Each owns its
own README; do not duplicate config here.

| Distribution | Bub entry point | Workspace path | README |
| --- | --- | --- | --- |
| `agentseek-ag-ui` | n/a | `contrib/agentseek-ag-ui` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-ag-ui/README.md) |
| `agentseek-cli` | `cli` | `contrib/agentseek-cli` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-cli/README.md) |
| `agentseek-langchain` | `langchain` | `contrib/agentseek-langchain` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-langchain/README.md) |
| `agentseek-observability` | `observability` | `contrib/agentseek-observability` | [README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-observability/README.md) |
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
contrib/agentseek-observability
contrib/agentseek-schedule-sqlalchemy
contrib/agentseek-tapestore-oceanbase
contrib/agentseek-contextseek
.agentseek/agentseek-project
```

The trailing `.agentseek/agentseek-project` is the **default plugin sandbox**;
including it as a workspace member lets uv resolve plugins installed by
`agentseek install` against the same lockfile (`pyproject.toml:109`).

## Skills bundled at build time

`[tool.pdm.build].skills` (`pyproject.toml:78`):

| Source | Subpath | Skills included |
| --- | --- | --- |
| `git+https://github.com/PsiACE/skills.git` | `skills` | `friendly-python`, `piglet` |

These ship inside the wheel under the top-level `skills/` package, alongside
the project's own `src/skills/` contents.

## Index URL

`[tool.uv]` pins `index-url = "https://pypi.org/simple"`
(`pyproject.toml:85`). For faster dev installs, set `UV_INDEX_URL` to a
mirror (e.g. `https://pypi.tuna.tsinghua.edu.cn/simple`).

## See also

- How-to: `../how-to/install-a-plugin.md`,
  `../how-to/author-a-contrib-plugin.md`
- Reference: `cli.md`, `file-layout.md`
