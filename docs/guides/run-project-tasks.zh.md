---
title: 运行项目任务
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-07-07
sources:
  - src/agentseek/cli/commands/task.py
  - src/agentseek/cli/lifecycle/core.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/agentic-rag/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
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

## 推荐的 Agent 技能包

有些模板会暴露可选任务，用来为编码 Agent 安装外部技能包。这仍然是
项目任务，不是新的 AgentSeek 根命令。

OceanBase seekdb 相关模板会暴露：

```bash
agentseek task seekdb-skills
```

这个任务会运行：

```bash
npx skills add oceanbase/seekdb-ecology-plugins --all
```

用途：为支持的编码 Agent 安装推荐的 OceanBase seekdb 技能，帮助处理
OceanBase seekdb 搭建、使用和排障。

前置条件：Node.js 与 `npx`、访问 npm registry 和技能包仓库的网络、
以及外部 `skills` CLI 支持的编码 Agent。命令语法已在 2026-07-07
按 `skills` npm 包 README 校验。

在生成项目内运行 `agentseek task --list`，即可确认当前模板是否提供这个任务。

## 下一步

- [理解生命周期规范](../reference/lifecycle-spec.md)
- [查看所有命令选项](../reference/cli.md)
