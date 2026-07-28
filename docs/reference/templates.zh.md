---
title: 模板
type: reference
audience: [A1, A2]
runs: no
verified_on: 2026-07-28
sources:
  - src/agentseek/data/catalog-lock.json
  - src/agentseek/cli/catalog.py
  - src/agentseek/cli/commands/create.py
  - https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0
---

# 模板

## 默认模板目录

AgentSeek 0.1.0 使用独立的
[`agentseek-ai/agentseek-templates`](https://github.com/agentseek-ai/agentseek-templates)
模板目录。安装后的 wheel 内嵌以下不可变坐标：

| 坐标 | 值 |
| --- | --- |
| 模板目录 release | `v0.1.0` |
| 模板目录 commit | `494863bc1b9aab19f9885d716c03ce654fb26014` |
| 生命周期版本 | `2` |
| Core 依赖快照 | `core-snapshot-v0.1.0` |
| Core 依赖 commit | `883addad1e2993c4be6fc8ba053f87f25fb5057a` |

列出、过滤和交互选择直接读取 wheel 内嵌的注册表快照，不需要下载目录。
描述或生成命名模板时，CLI 会获取精确目录 commit 的仓库归档，并以 wheel
内嵌的可信子树摘要验证模板内容，再把选中的模板原子写入缓存。部分、过期、
被篡改或元数据不匹配的缓存不会被复用。

默认解析器不会选择 core 源码 checkout 中的生命周期 v1 镜像，也不会回退
到可变的 `main`。core 镜像只为已发布的 0.0.x 客户端和显式本地路径保留。

## 可用模板

| 模板 | 描述 |
| --- | --- |
| `bub/default` | 带 AgentSeek 生命周期规范的轻量 Bub agent。 |
| `deepagents/content-builder` | 带写作流程、图像生成、本地 UI 和 AgentSeek 生命周期规范的 DeepAgents 内容构建器。 |
| `deepagents/default` | 带 AgentSeek 生命周期规范的最小 DeepAgents 应用。 |
| `deepagents/mcp` | DeepAgents MCP Tools 应用，提供经过校验的 stdio/HTTP 配置、本地计算器示例、流式 UI 和 AgentSeek 生命周期规范。 |
| `deepagents/research` | 带检索流程、本地 UI 和 AgentSeek 生命周期规范的 DeepAgents research 应用。 |
| `deepagents/sandbox` | DeepAgents sandbox coding agent，默认接入 Daytona，并提供收费的 LangSmith Sandbox 备选、本地 UI 和 AgentSeek 生命周期规范。 |
| `langchain/agentic-rag` | 带 OceanBase vector search 和 AgentSeek 生命周期规范的 LangChain agentic RAG。 |
| `langchain/agentic-rag-hybrid` | 基于 LangChain 的 Agentic Hybrid RAG 模板，包含图片导入、向量/稀疏/全文/元数据混合检索、对比演示、可选 Phoenix 可观测性和 AgentSeek 生命周期配置。 |
| `langchain/agentic-rag-openvino` | 带本地 OpenVINO models 和 AgentSeek 生命周期规范的 LangChain local RAG。 |
| `langchain/cli-remote` | 把本地生命周期工作流连接到远程 LangGraph 服务的 LangChain 模板。 |
| `langchain/default` | 带本地 Web UI 和 AgentSeek 生命周期规范的 LangChain agent 应用。 |
| `langchain/markdown-messages` | 带 Markdown 消息渲染和 AgentSeek 生命周期规范的 LangChain chat 应用。 |

## 模板 spec

| 形式 | 示例 |
| --- | --- |
| Type | `bub` |
| Type and name | `bub/default` |
| Absolute local path | `/path/to/template` |
| Git URL | `https://github.com/example/templates.git` |

## 显式模板目录仓库

| 形式 | 结果 |
| --- | --- |
| `agentseek create --template-repo <https-url> --checkout <sha> --list-templates` | 列出指定 commit 上的显式 AgentSeek 模板目录。 |
| `agentseek create --template-repo <https-url> --checkout <sha> --filter rag --list-templates` | 过滤同一显式模板目录 commit。 |
| `agentseek create langchain/default --template-repo <https-url> --checkout <sha> --describe` | 描述同一显式模板目录 commit 上的命名模板。 |
| `agentseek create langchain/default --template-repo <https-url> --checkout <sha>` | 从同一显式模板目录 commit 生成项目。 |

`<https-url>` 标识包含 `templates/index.json` 的 AgentSeek 模板目录仓库。
`<sha>` 必须是完整的 40 个小写字符 Git commit SHA，并匹配 `[0-9a-f]{40}`。
显式模板目录不能与位置参数中的直接 Cookiecutter URL 或绝对路径组合。位置
参数 URL/路径的 passthrough 行为保持不变；只有 `--template-repo` 限定为 HTTPS。

规范化后的模板目录 URL 和精确 commit 标识缓存条目。AgentSeek 在复用前
验证缓存元数据。显式模板目录失败时，不回退到内置模板或本地 checkout。

列出、过滤和描述不执行 Cookiecutter hooks。生成操作信任模板内容，可能
执行其 hooks。生成项目中的 `_agentseek_source_url` 仍指向 AgentSeek 核心
仓库，而非模板目录仓库。

## 选择和发现

| 命令 | 结果 |
| --- | --- |
| `agentseek create` | 交互式选择类型和模板。 |
| `agentseek create --list-templates` | 列出所有已知模板。 |
| `agentseek create --list-templates --filter rag` | 只列出 spec 或描述匹配 `rag` 的模板。 |
| `agentseek create bub --list-templates` | 只列出 `bub` 模板。 |
| `agentseek create bub` | 解析到 `bub/default`。 |
| `agentseek create bub/default` | 使用指定模板。 |
| `agentseek create bub --template default` | 使用 `bub/default`。 |
| `agentseek create bub/default --output-dir ./generated` | 将生成项目写入所选目录下。 |
| `agentseek create --template` | 列出模板的兼容入口。新脚本优先使用 `--list-templates`。 |
