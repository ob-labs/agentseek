---
title: CLI 参考
type: reference
audience: [A2]
runs: no
verified_on: 2026-06-26
sources:
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/create.py
  - src/agentseek/cli/commands/dev.py
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/commands/info.py
  - src/agentseek/cli/commands/task.py
---

# CLI 参考

## 安装和调用

| 命令 | 说明 |
| --- | --- |
| `uv tool install agentseek` | 安装日常使用的 CLI。 |
| `agentseek ...` | 安装后运行生命周期命令。 |
| `uvx agentseek ...` | 不安装工具，只运行一次 AgentSeek 命令。 |

## 根选项

| 选项 | 说明 |
| --- | --- |
| `--mode [cli\|agent]` | 选择 CLI profile。当前文档化的生命周期工作流使用 `cli`。 |
| `--help` | 显示所选 profile 的帮助。 |

## 默认命令

| 命令 | 说明 |
| --- | --- |
| `agentseek create [spec]` | 从模板创建项目。 |
| `agentseek doctor` | 通过生命周期规范检查本地就绪状态。 |
| `agentseek dev` | 通过生命周期规范启动本地开发。 |
| `agentseek info` | 显示项目元数据和入口。 |
| `agentseek task` | 运行项目定义的生命周期规范任务。 |
| `agentseek version` | 显示 AgentSeek 版本信息。 |

## `create`

### 形式

| 形式 | 说明 |
| --- | --- |
| `agentseek create` | 交互式选择类型和模板。 |
| `agentseek create <type>` | 使用该类型的默认模板。 |
| `agentseek create <type>/<name>` | 使用指定模板。 |
| `agentseek create <url-or-absolute-path>` | 把 spec 直接传给 Cookiecutter。 |

内置模板类型集合当前是 `bub`、`deepagents` 和 `langchain`。

### 选项

| 选项 | 说明 |
| --- | --- |
| `spec` | 模板类型、`type/name`、Git URL 或绝对本地路径。 |
| `--list-templates` | 列出模板。带 `type` 时只列出该类型。 |
| `--template name` | 选择所选类型下的命名模板，例如 `bub --template default`。 |
| `--template` | 列出模板的兼容入口。新脚本优先使用 `--list-templates`。 |
| `--checkout ref` | 拉取远程模板源时使用分支、tag 或 commit。 |
| `--no-input` | 跳过 Cookiecutter 变量提示，使用模板默认值。 |

### 缺失模板

| 形式 | 行为 |
| --- | --- |
| `agentseek create bub --template missing` | 以代码 `2` 退出，并显示缺失模板和支持的 `bub` 模板。 |
| `agentseek create bub/missing` | 以代码 `2` 退出，并显示缺失模板和支持的 `bub` 模板。 |

## `doctor`

| 选项 | 说明 |
| --- | --- |
| `--live` | 检查已经运行的本地服务。 |
| `--strict` | 把警告视为失败。 |

## `dev`

| 选项 | 说明 |
| --- | --- |
| `--dry-run` | 打印启动计划，不启动服务。 |
| `--skip-check` | 启动前跳过预先的 strict `doctor` 检查。核心必需输入仍会检查。 |

## `info`

| 选项 | 说明 |
| --- | --- |
| `--verbose` | 显示生命周期 loader 发现细节。 |

## `task`

| 形式 | 说明 |
| --- | --- |
| `agentseek task --list` | 列出项目定义的生命周期规范任务。 |
| `agentseek task --help` | 显示 AgentSeek task 边界。 |
| `agentseek task <name>` | 运行项目定义的生命周期规范任务。 |

`task` 必须从包含 `.agentseek/lifecycle.toml` 的项目目录运行。
