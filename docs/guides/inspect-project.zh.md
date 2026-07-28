---
title: 查看项目
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-07-28
sources:
  - src/agentseek/cli/commands/info.py
  - src/agentseek/cli/lifecycle/json_output.py
  - https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0
---

# 查看项目

在生成项目目录中运行 `info`。

```bash
agentseek info
```

```text title="输出片段"
Project
  Root: /path/to/my_bub_agent
  Name: My Bub Agent
  Template: bub/default
  Lifecycle: .agentseek/lifecycle.toml / version 2

Entrypoints
  Dev: agentseek dev
  App: http://127.0.0.1:5173
  Gateway: http://127.0.0.1:8088/agent
  Copilotkit: http://127.0.0.1:4000/api/copilotkit

Environment
  Env file: .env (present)
  BUB_MODEL: set (.env)
  BUB_API_KEY: set (.env)

Lifecycle Tasks
  frontend: Install frontend dependencies.

Next
  agentseek task --list
  agentseek doctor
  agentseek dev
```

这些入口和项目任务来自生命周期规范。

```toml title=".agentseek/lifecycle.toml 片段"
[services.app]
url = "http://127.0.0.1:5173"

[services.gateway]
url = "http://127.0.0.1:8088/agent"

[services.copilotkit]
url = "http://127.0.0.1:4000/api/copilotkit"
```

需要 loader 细节时使用 verbose 模式。

```bash
agentseek info --verbose
```

```text title="输出片段"
Capabilities
  commands: dev, info, doctor
  tasks: frontend

Discovery
  Python: /path/to/python
  uv: /path/to/uv
  node: /path/to/node
  npm: /path/to/npm
```

## 供 Desktop 或其他工具读取

其他程序需要稳定的服务拓扑和操作时，使用 JSON 模式。

```bash
agentseek info --json
```

返回值是一个紧凑 JSON 文档，包含 `schema_version`、生命周期版本、规范化
`services` 以及可直接使用的 `actions`。消费者应使用这些结构化动作，而不是
解析人类输出或自行推断哪些 URL 可以打开。输出不包含环境变量值、原始命令、
不安全 URL 或主机绝对路径。

## 下一步

- [检查项目](check-project.md)
- [运行本地开发](run-local-development.md)
