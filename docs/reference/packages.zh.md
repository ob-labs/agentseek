---
title: 包参考
type: reference
audience: [A2, A3, A4]
runs: no
verified_on: 2026-06-08
sources:
  - pyproject.toml
  - contrib/README.md
---

# 包参考

AgentSeek 发布一个顶层 Python 包：`agentseek`。该包同时提供 CLI 工具和可嵌入的
harness 库。

| 字段 | 值 | 来源 |
| --- | --- | --- |
| Name | `agentseek` | `pyproject.toml` |
| Version | `0.0.2` | `pyproject.toml` |
| Python | `>=3.12,<4.0` | `pyproject.toml` |
| Console script | `agentseek = "agentseek.__main__:app"` | `pyproject.toml` |
| Build backend | `pdm.backend` | `pyproject.toml` |
| Build includes | `src/agentseek`, `src/skills` | `pyproject.toml` |

## 核心依赖

运行时依赖同时覆盖 harness runtime 和项目命令工具：

| Package | 用途 |
| --- | --- |
| `bub` | hook-first runtime、channels、plugins 和 CLI 基础。 |
| `cookiecutter` | `agentseek create` 的模板渲染。 |
| `jinja2` | 模板渲染支持。 |
| `logfire` | 本地 instrumentation 和日志集成。 |
| `npx-skills` | `agentseek skills` 使用的 skill CLI wrapper。 |
| `pydantic-settings` | 运行时配置。 |
| `typer` | CLI 构建。 |

## Contrib 包

Contrib 包是可选扩展，可通过 `agentseek plugin install <package>` 安装，
也可以由生成项目直接依赖。

| Package | Bub entry point | Workspace path |
| --- | --- | --- |
| `agentseek-ag-ui` | n/a | `contrib/agentseek-ag-ui` |
| `agentseek-langchain` | `langchain` | `contrib/agentseek-langchain` |
| `agentseek-tapestore-oceanbase` | `tapestore-oceanbase` | `contrib/agentseek-tapestore-oceanbase` |
| `agentseek-schedule-sqlalchemy` | `schedule` | `contrib/agentseek-schedule-sqlalchemy` |
| `agentseek-contextseek` | `contextseek` | `contrib/agentseek-contextseek` |

每个 contrib package 在自己的 `[project.entry-points.bub]` 下声明入口点。

## uv workspace 成员

```text
contrib/agentseek-ag-ui
contrib/agentseek-langchain
contrib/agentseek-schedule-sqlalchemy
contrib/agentseek-tapestore-oceanbase
contrib/agentseek-contextseek
.agentseek/agentseek-project
```

`.agentseek/agentseek-project` 是默认插件 sandbox。作为 workspace member 保留，
可以让开发期间安装的插件继续使用同一份 lockfile 解析。

## 内置 skills

`[tool.pdm.build].skills` 会把以下 skills 打进 wheel：

| Source | Subpath | Skills included |
| --- | --- | --- |
| `git+https://github.com/PsiACE/skills.git` | `skills` | `friendly-python`, `piglet` |

## 相关

- [CLI 参考](cli.zh.md)
- [文件布局参考](file-layout.zh.md)
- [安装插件](../how-to/install-a-plugin.zh.md)
