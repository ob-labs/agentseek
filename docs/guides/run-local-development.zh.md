---
title: 运行本地开发
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-26
sources:
  - src/agentseek/cli/commands/dev.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# 运行本地开发

在生成项目目录里，用已安装的 CLI 启动开发栈。
如果期望启动不遇到设置错误，先运行 `agentseek doctor`。

```bash
agentseek dev
```

不启动服务，只预览启动计划。

```bash
agentseek dev --dry-run
```

```text title="输出片段"
Startup plan
  Gateway: uv run bub gateway --enable-channel ag-ui
  Frontend: npm run dev
  App: http://127.0.0.1:5173
  Gateway: http://127.0.0.1:8088/agent
  Copilotkit: http://127.0.0.1:4000/api/copilotkit
```

启动计划来自 process 和 service 声明。

```toml title=".agentseek/lifecycle.toml 片段"
[processes.gateway]
command = ["uv", "run", "bub", "gateway", "--enable-channel", "ag-ui"]

[processes.frontend]
command = ["npm", "run", "dev"]
cwd = "frontend"

[services.app]
url = "http://127.0.0.1:5173"
```

当你已经知道项目状态时，可以跳过预先的 strict `doctor` 检查。
生命周期规范声明的核心必需输入，仍会在进程启动前检查。

```bash
agentseek dev --skip-check
```

使用 `Ctrl+C` 停止本地开发栈。

## 下一步

- [检查运行中的服务](check-project.md)
- [运行项目任务](run-project-tasks.md)
