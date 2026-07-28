---
title: 模板
type: reference
audience: [A1, A2]
runs: no
verified_on: 2026-07-28
sources:
  - templates/index.json
  - src/agentseek/cli/commands/create.py
  - templates/deepagents/sandbox/README.md
---

# 模板

## 可用模板

| 模板 | 描述 |
| --- | --- |
| `bub/default` | 带 AgentSeek 生命周期规范的轻量 Bub agent。 |
| `deepagents/content-builder` | 带写作流程、图像生成、本地 UI 和 AgentSeek 生命周期规范的 DeepAgents 内容构建器。 |
| `deepagents/default` | 带 AgentSeek 生命周期规范的最小 DeepAgents 应用。 |
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
