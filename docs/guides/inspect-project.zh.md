---
title: 查看项目
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-26
sources:
  - src/agentseek/cli/commands/info.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
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
  Lifecycle: .agentseek/lifecycle.toml / version 1

Entrypoints
  Dev: agentseek dev
  App: http://127.0.0.1:5173
  Gateway: http://127.0.0.1:8088/agent
  Copilotkit: http://127.0.0.1:4000/api/copilotkit

Environment
  Env file: .env (present)
  BUB_MODEL: set (.env)
  BUB_API_KEY: set (.env)
```

这些入口来自生命周期规范。

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

## 下一步

- [检查项目](check-project.md)
- [运行本地开发](run-local-development.md)
