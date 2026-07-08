---
title: 生命周期规范
type: reference
audience: [A2]
runs: no
verified_on: 2026-06-26
sources:
  - src/agentseek/cli/lifecycle/spec.py
  - src/agentseek/cli/lifecycle/core.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# 生命周期规范

## 文件

AgentSeek 从当前目录向上查找生命周期规范：

```text
.agentseek/lifecycle.toml
```

其他项目文件不参与生命周期发现。

## 形状

```toml
version = 1
template = "bub/default"
name = "My Bub Agent"
env_file = ".env"

[tools]
required = ["uv", "node", "npm"]

[paths]
required = ["frontend/package.json", "frontend/node_modules"]

[env.BUB_MODEL]
required = true
default = "openai:gpt-4o-mini"

[env.BUB_API_KEY]
required = true
aliases = ["BUB_OPENAI_API_KEY"]

[services.app]
url = "http://127.0.0.1:5173"

[processes.frontend]
command = ["npm", "run", "dev"]
cwd = "frontend"

[checks.frontend]
type = "http"
target = "http://127.0.0.1:5173"
timeout = 2
attempts = 3

[tasks.frontend]
description = "Install frontend dependencies."
command = ["npm", "install", "--prefix", "frontend"]
```

## 段落

| 段落 | 作用 |
| --- | --- |
| `env_file` | 可选项目本地 env 文件，只用于声明的环境检查。它不会注入子进程。 |
| `tools` | 项目需要的可执行文件。 |
| `paths` | 必需的本地文件或目录。 |
| `env.<name>` | AgentSeek 应检查的环境变量。默认值优先级低于 `env_file` 和 shell 变量。 |
| `services.<name>` | `agentseek info` 展示的公开本地服务端点。 |
| `processes.<name>` | `agentseek dev` 启动的长运行命令。 |
| `checks.<name>` | `agentseek doctor --live` 使用的 HTTP live 就绪检查。2xx 和 3xx 响应成功。 |
| `tasks.<name>` | `agentseek task <name>` 运行的一次性任务。`cwd` 是项目相对路径，且必须存在。 |

## 环境检查

AgentSeek 从生命周期默认值、可选 `env_file` 和当前进程环境检查环境需求：

```text
lifecycle default < env_file < shell environment
```

只有 `[env.<name>]` 下声明的 key 及其 aliases 会从 `env_file` 读取。
模板不需要声明项目可能使用的每一个运行时变量。AgentSeek 不会把 env 文件或
生命周期默认值传给子进程。

## 第一阶段范围

Version 1 支持必需工具、必需路径、项目环境需求、HTTP live 检查、长运行进程和一次性任务。
它不支持可选 tool/path 检查、TCP 检查、进程级环境覆盖、多个 env 文件或 env 插值。

## 公开命令

| 命令 | 行为 |
| --- | --- |
| `agentseek info [--verbose]` | 打印生命周期规范里的项目事实。 |
| `agentseek doctor [--live] [--strict]` | 检查 tools、paths、env 和可选 live endpoints。 |
| `agentseek dev [--dry-run] [--skip-check]` | 打印或启动声明的开发进程。`--skip-check` 只跳过预先的 strict `doctor` 检查。 |
| `agentseek task --list` | 列出 `tasks` 下声明的任务。 |
| `agentseek task <name>` | 运行一个声明的一次性任务。 |

## 错误

| 条件 | 结果 |
| --- | --- |
| 缺少 `.agentseek/lifecycle.toml` | Exit code `2`。 |
| 生命周期规范版本不支持 | Exit code `2`。 |
| 生命周期规范无效 | Exit code `2`。 |
