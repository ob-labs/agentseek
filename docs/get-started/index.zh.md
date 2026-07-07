---
title: 快速开始
type: tutorial
audience: [A1, A2]
runs: yes
verified_on: 2026-06-26
sources:
  - pyproject.toml
  - README.md
  - templates/index.json
  - templates/bub/default/cookiecutter.json
---

# 快速开始

创建一个应用，安装它的本地依赖，并启动开发流程。

## 安装 CLI

```bash
uv tool install agentseek
```

## 创建应用

```bash
agentseek create bub/default --no-input
cd my_bub_agent
```

`bub/default` 是一个可用模板路径。其他模板也可以使用同一套生命周期命令。

## 准备项目

```bash
cp .env.example .env
$EDITOR .env
uv sync
npm install --prefix frontend
```

在 `.env` 或运行 AgentSeek 的环境里，设置所选模板需要的模型和 provider 凭证。

AgentSeek 只把 `.env` 用作模板声明的生命周期环境检查来源。
它不会把 `.env` 自动传给子进程。

## 检查并运行

准备好 `.env` 和本地依赖后，再运行就绪检查。

```bash
agentseek doctor
agentseek dev
```

使用 `Ctrl+C` 停止本地开发栈。

## 下一步

- [用其他模板创建项目](../guides/create-project.md)
- [检查本地就绪状态](../guides/check-project.md)
- [查看命令表面](../reference/cli.md)
