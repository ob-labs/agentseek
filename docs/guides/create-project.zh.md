---
title: 创建项目
type: how-to
audience: [A1, A2]
runs: yes
verified_on: 2026-06-26
sources:
  - pyproject.toml
  - src/agentseek/cli/commands/create.py
  - templates/index.json
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
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

这个非交互形式成功时不会打印输出。生成项目中会包含后续命令读取的
生命周期规范。

```text title="生成文件片段"
my_bub_agent/
  .agentseek/lifecycle.toml
  .env.example
  frontend/package.json
```

```toml title=".agentseek/lifecycle.toml 片段"
version = 1
template = "bub/default"
name = "My Bub Agent"
env_file = ".env"
```

进入生成目录。

```bash
cd my_bub_agent
```

## 列出模板

```bash
agentseek create --list-templates
```

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
