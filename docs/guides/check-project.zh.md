---
title: 检查项目
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-07-28
sources:
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/lifecycle/diagnostics.py
  - src/agentseek/cli/lifecycle/json_output.py
  - https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0
---

# 检查项目

在生成项目目录里，用已安装的 CLI 运行就绪检查。
如果期望检查通过，先准备 `.env` 并运行 `agentseek task frontend`。

```bash
agentseek doctor
```

```text title="输出片段"
ok   lifecycle.toml: Lifecycle spec is present.
ok   uv: uv is available.
ok   node: node is available.
ok   npm: npm is available.
ok   frontend/package.json: frontend/package.json is present.
ok   frontend/node_modules: frontend/node_modules is present.
ok   .env: .env is present.
ok   BUB_MODEL: BUB_MODEL is configured.
ok   BUB_API_KEY: BUB_API_KEY or BUB_OPENAI_API_KEY is configured.
ok   gateway cwd: . is present.
ok   frontend cwd: frontend is present.
```

这些检查来自必需工具、路径和环境变量声明。

```toml title=".agentseek/lifecycle.toml 片段"
[tools]
required = ["uv", "node", "npm"]

[paths]
required = ["frontend/package.json", "frontend/node_modules"]

[env.BUB_API_KEY]
required = true
aliases = ["BUB_OPENAI_API_KEY"]
```

在自动化里使用 strict 模式，让警告也导致检查失败。

```bash
agentseek doctor --strict
```

应用启动后使用 live 模式。它检查本地服务是否正在监听。

```bash
agentseek doctor --live
```

```text title="输出片段"
ok   gateway: http://127.0.0.1:8088/agent/health is reachable.
ok   copilotkit: http://127.0.0.1:4000/health is reachable.
ok   frontend: http://127.0.0.1:5173 is reachable.
```

Live 检查使用项目声明的服务健康检查目标。

```toml title=".agentseek/lifecycle.toml 片段"
[checks.gateway]
type = "http"
target = "http://127.0.0.1:8088/agent/health"
timeout = 2
attempts = 3
```

## 在自动化中使用诊断结果

需要稳定的类型化结果列表时使用 JSON 模式。服务已启动时加上 `--live`。

```bash
agentseek doctor --json
agentseek doctor --live --json
```

完成的诊断运行使用 `ok: true`。通过 `data.passed` 和进程退出码判断检查是否
通过；没有 `--live` 时，声明的实时检查状态为 `not_run`。JSON 模式只向 stdout
写入一个文档，不向 stderr 混入诊断文本。

不要把 `--strict` 和 `--json` 组合使用；该选项冲突会返回退出码 `2` 和结构化
错误 envelope。

## 下一步

- [启动应用](run-local-development.md)
- [运行项目任务](run-project-tasks.md)
- [查看所有命令选项](../reference/cli.md)
