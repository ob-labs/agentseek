---
title: 本地执行模式
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-25
sources:
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/dev.py
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/commands/task.py
---

# 本地执行模式

当你需要为生成的 AgentSeek 项目选择正确的本地入口时，使用本页。这里概览项目生命周期命令，不重复完整的 [CLI 参考](../reference/cli.zh.md)。

## 选择入口

| 目标 | 命令 | 运行位置 |
| --- | --- | --- |
| 检查项目文件、环境、依赖和可选 live service | `agentseek doctor` | 生成项目根目录 |
| 预览开发启动计划 | `agentseek dev --dry-run` | 生成项目根目录 |
| 启动本地开发栈 | `agentseek dev` | 生成项目根目录 |
| 启动前跳过预先 strict doctor 检查 | `agentseek dev --skip-check` | 生成项目根目录 |
| 列出模板定义的任务 | `agentseek task --list` | 生成项目根目录 |
| 运行一个模板定义的任务 | `agentseek task <name>` | 生成项目根目录 |

## 就绪检查：`agentseek doctor`

在启动开发栈前使用 `agentseek doctor`，快速发现缺失文件、环境变量、依赖和端口问题。

```bash
agentseek doctor
```

需要更强验证时，使用 strict 或 live 检查。

```bash
agentseek doctor --strict
agentseek doctor --live
```

完整就绪检查流程见[检查项目](check-project.zh.md)。

## 开发栈：`agentseek dev`

当你需要 AgentSeek 启动生命周期规范中声明的长运行进程时，使用 `agentseek dev`。

```bash
agentseek dev
```

只预览启动计划，不启动进程。

```bash
agentseek dev --dry-run
```

只有在已经了解项目状态时，才跳过预先的 strict `doctor` 检查。

```bash
agentseek dev --skip-check
```

生成启动计划示例见[运行本地开发](run-local-development.zh.md)。

## 项目任务：`agentseek task`

对于模板声明的一次性命令，例如依赖安装、前端设置或检查，使用 `agentseek task`。

```bash
agentseek task --list
agentseek task frontend
```

任务示例和预期输出见[运行项目任务](run-project-tasks.zh.md)。

## 相关页面

- [检查项目](check-project.zh.md)
- [运行本地开发](run-local-development.zh.md)
- [运行项目任务](run-project-tasks.zh.md)
- [CLI 参考](../reference/cli.zh.md)
