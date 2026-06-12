---
title: 包参考
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-06-12
sources:
  - pyproject.toml
  - contrib/README.md
---

# 包参考

## 发布包

| 字段 | 值 |
| --- | --- |
| Package name | `agentseek` |
| Version | `0.0.2` |
| Python | `>=3.12,<4.0` |
| Console script | `agentseek = "agentseek.__main__:app"` |
| Build backend | `pdm.backend` |
| Build includes | `src/agentseek`, `src/skills` |

## 运行时依赖

| Package | 用途 |
| --- | --- |
| `bub` | Runtime kernel、channels、plugins 和 CLI foundation。 |
| `cookiecutter` | `agentseek create` 的模板渲染。 |
| `jinja2` | 模板渲染支持。 |
| `logfire` | Instrumentation 和日志集成。 |
| `npx-skills` | `agentseek skills` 使用的 skill CLI wrapper。 |
| `pydantic-settings` | 运行时设置。 |
| `typer` | CLI 构建。 |

## Dependency groups

| Group | 内容 |
| --- | --- |
| `dev` | Tests、type checks、docs 和 example development。 |
| `plugins` | 开发 workspace 时使用的 plugin packages。 |

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
