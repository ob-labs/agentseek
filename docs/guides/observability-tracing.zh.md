---
title: 可观测性和追踪
type: how-to
audience: [A2, A4]
runs: no
verified_on: 2026-07-07
sources:
  - src/agentseek/env.py
  - src/agentseek/__main__.py
  - templates/langchain/default/{{cookiecutter.project_slug}}/.env.example
  - templates/langchain/default/{{cookiecutter.project_slug}}/README.md
  - templates/langchain/default/{{cookiecutter.project_slug}}/docker-compose.yml
  - templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/.env.example
  - templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/README.md
  - templates/langchain/agentic-rag-hybrid/{{cookiecutter.project_slug}}/docker-compose.yml
  - templates/deepagents/research/{{cookiecutter.project_slug}}/.env.example
  - templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.env.example
  - templates/langchain/sandbox/{{cookiecutter.project_slug}}/.env.example
---

# 可观测性和追踪

当本地运行正常，但 trace 或诊断输出没有出现在预期位置时，使用这个指南。

## 选择 trace 目标

| 目标 | 适合场景 | 配置入口 |
| --- | --- | --- |
| LangSmith cloud | 需要托管的 LangChain 或 LangGraph traces。 | `.env` 或 shell 中的 `LANGSMITH_*` 变量。 |
| AgentSeek console | 需要本地 CLI 诊断 spans 和 events。 | `AGENTSEEK_CONSOLE=true`。 |
| Phoenix | 使用 `langchain/default` 或 `langchain/agentic-rag-hybrid` 并需要本地 OpenTelemetry traces。 | `AGENTSEEK_OTEL_*` 变量和模板 compose stack。 |

这些目标彼此独立。启用其中一个不会把数据发送到另一个。

## 配置 LangSmith cloud tracing

设置 LangChain 和 LangGraph 模板会读取的 LangSmith 变量。

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<your-langsmith-api-key>
LANGSMITH_PROJECT=<your-project-name>
```

当 API key 属于非默认区域时，设置 `LANGSMITH_ENDPOINT`。APAC key 使用
APAC endpoint。

```env
LANGSMITH_ENDPOINT=https://apac.api.smith.langchain.com
```

LangSmith observability quickstart 也说明了同一类区域 endpoint 行为：
非 US 区域需要 `LANGSMITH_ENDPOINT`，否则 API key 可能无法通过默认
endpoint 认证。

[ob-labs/agentseek#83](https://github.com/ob-labs/agentseek/issues/83)
记录了促成本指南的 APAC 故障模式。

## 排查本地 Studio 可见但 cloud traces 缺失

本地 Studio 或本地 thread 页面能显示来自本地开发服务的运行，即使 cloud
trace ingestion 正在失败。

当 Studio 可见但 LangSmith cloud traces 缺失时，按这个表排查。

| 检查项 | 修复方式 |
| --- | --- |
| `LANGSMITH_TRACING` 不是 `true` | 在启动应用的同一个环境中启用 tracing。 |
| `LANGSMITH_API_KEY` 为空或来自其他区域 | 使用目标 LangSmith 区域的 API key。 |
| APAC 或其他非默认区域缺少 `LANGSMITH_ENDPOINT` | 显式设置区域 endpoint。 |
| `LANGSMITH_PROJECT` 和打开的 dashboard project 不一致 | 打开已配置的 project，或修改变量。 |
| 应用进程没有加载 `.env` | 在启动应用的 shell 中导出这些变量。 |

把本地 Studio 可见视为本地运行时信号。把 cloud traces 视为单独的
ingestion 信号。

## 启用 AgentSeek console 输出

当你希望 AgentSeek CLI spans 和 events 通过 Logfire console 在本地渲染时，
设置 `AGENTSEEK_CONSOLE=true`。

```env
AGENTSEEK_CONSOLE=true
```

AgentSeek 使用 `send_to_logfire=False` 配置 Logfire，所以这不会上传数据到
Logfire cloud。它只改变 AgentSeek CLI 进程的本地 console 渲染。

## 在 `langchain/default` 中使用 Phoenix

`langchain/default` 模板包含导出到本地 Phoenix 的 OpenTelemetry tracing。
生成应用会在 LangChain application process 中注册 tracing。Bub 和 gateway
只转发消息。

compose stack 会从 app container 内部把 spans 发送到 Phoenix。

```env
AGENTSEEK_OTEL_ENABLED=true
AGENTSEEK_OTEL_SERVICE_NAME=<project-slug>
AGENTSEEK_OTEL_PROJECT_NAME=<project-slug>
AGENTSEEK_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://phoenix:6006/v1/traces
```

非 compose 运行时，把 endpoint 指向 localhost。

```env
AGENTSEEK_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:6006/v1/traces
```

模板 compose stack 使用 `ghcr.io/agentseek-ai/agentseek-phoenix:main`
运行 Phoenix，并通过 OceanBase seekdb（`quay.io/oceanbase/seekdb:latest`）
持久化 Phoenix 数据。可以用 `.env` 中的 `AGENTSEEK_PHOENIX_IMAGE` 和
`OCEANBASE_SEEKDB_IMAGE` 覆盖默认镜像。

## 在 `langchain/agentic-rag-hybrid` 中使用 Phoenix

Hybrid 模板默认保持 `agentseek dev` 轻量，只启动 `uv`、`langgraph dev`
和 Vite frontend。Phoenix 是可选 tracing stack：

```bash
agentseek task phoenix
```

然后在 `.env` 中启用 OTEL，再启动 `agentseek dev`。

```env
AGENTSEEK_OTEL_ENABLED=true
AGENTSEEK_OTEL_SERVICE_NAME=<project-slug>
AGENTSEEK_OTEL_PROJECT_NAME=<project-slug>
AGENTSEEK_OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1:6006/v1/traces
```

生成项目的 `/custom/observability` 路由会返回当前 OTEL endpoint、
Phoenix URL 和 Phoenix 使用的 OceanBase seekdb URL。Phoenix trace 存储
使用 compose stack；hybrid retrieval 仍然通过 `langchain-oceanbase` 使用
embedded SeekDB。

## 相关内容

- [生命周期规范参考](../reference/lifecycle-spec.md)
- [模板参考](../reference/templates.md)
- [运行本地开发](run-local-development.md)
- [LangSmith observability quickstart](https://docs.langchain.com/langsmith/observability-quickstart)
