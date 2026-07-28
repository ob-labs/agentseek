---
title: 创建项目
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-07-28
sources:
  - pyproject.toml
  - src/agentseek/data/catalog-lock.json
  - src/agentseek/cli/commands/create.py
  - https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0
---

# 创建项目

用显式模板路径创建项目。

运行日常生命周期命令前，先安装 CLI。

```bash
uv tool install agentseek
```

```bash
agentseek create bub/default --no-input
```

这个非交互形式成功时会打印生成目录，以及下一步可运行的生命周期命令。

```text
Created my_bub_agent

Next:
  cd my_bub_agent
  agentseek info
  agentseek task --list
  agentseek doctor
```

生成项目中会包含后续命令读取的生命周期规范。

```text title="生成文件片段"
my_bub_agent/
  .agentseek/lifecycle.toml
  .env.example
  frontend/package.json
```

```toml title=".agentseek/lifecycle.toml 片段"
version = 2
template = "bub/default"
name = "My Bub Agent"
description = "Bub agent with a browser UI, CopilotKit runtime, and AG-UI gateway."
env_file = ".env"
guide = "README.md"
```

准备查看或运行项目时，进入生成目录。

```bash
cd my_bub_agent
```

## 列出模板

```bash
agentseek create --list-templates
```

列表直接读取 AgentSeek 0.1.0 内嵌的注册表快照，因此可以离线使用。只有在描述或
创建所选模板时，CLI 才会按自身记录的不可变 catalog commit 下载生命周期 v2 模板。

共享 CLI 当前识别 `bub`、`deepagents` 和 `langchain` 三种模板类型。
把类型放在 `--list-templates` 前面，可以只列出一个类型。

```bash
agentseek create bub --list-templates
```

## 按类型选择模板

每个 create 形式都应从一个不会已有同名生成目录的位置运行。

```bash
agentseek create bub --template default --no-input
```

## 兼容入口

```bash
agentseek create --template
```

不带值的 `--template` 会列出模板。新脚本优先使用 `--list-templates`。

## 下一步

- [查看项目](inspect-project.md)
- [检查项目](check-project.md)
- [运行本地开发](run-local-development.md)
