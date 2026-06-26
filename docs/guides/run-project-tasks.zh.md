---
title: 运行项目任务
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-06-26
sources:
  - src/agentseek/cli/commands/task.py
  - src/agentseek/cli/lifecycle/core.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# 运行项目任务

用已安装的 CLI 列出生成项目暴露的任务。

```bash
agentseek task --list
```

```text title="输出片段"
  frontend              Install frontend dependencies.
```

任务列表来自生命周期规范中的 `[tasks.*]` 条目。

```toml title=".agentseek/lifecycle.toml 片段"
[tasks.frontend]
description = "Install frontend dependencies."
command = ["npm", "install", "--prefix", "frontend"]
```

按名称运行项目任务。

```bash
agentseek task frontend
```

```text title="输出片段"
added 945 packages, and audited 946 packages in 1m
```

这个命令会从项目根目录运行声明的命令。完成后，`agentseek doctor`
会报告 `frontend/node_modules` 已存在。

任务由生成项目的生命周期规范声明。如果任务声明了 `cwd`，AgentSeek
会从这个项目相对目录运行命令，并在目录缺失时报生命周期错误。

## 下一步

- [理解生命周期规范](../reference/lifecycle-spec.md)
- [查看所有命令选项](../reference/cli.md)
