---
title: 模板编写规范
type: reference
audience: [A2, A3]
runs: no
verified_on: 2026-07-10
sources:
  - templates/index.json
  - src/agentseek/cli/lifecycle/spec.py
  - src/agentseek/cli/lifecycle/core.py
  - tests/cli_commands/test_templates_registry.py
  - tests/cli_commands/test_templates_render.py
  - "templates/langchain/agentic-rag/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.env.example"
---

# 模板编写规范

本规范适用于新增模板或对现有模板进行较大调整。框架实现可以不同，但生成项目必须保持统一的 AgentSeek 接口。

## 必需结构

| 路径 | 要求 | 验证依据 |
| --- | --- | --- |
| `templates/<type>/<name>/cookiecutter.json` | 必需。定义渲染参数和默认值。 | `test_templates_render.py` 中的模板发现逻辑。 |
| `templates/<type>/<name>/README.md` | 必需。说明模板用途和渲染参数。 | `test_registered_templates_have_readme`。 |
| `templates/<type>/<name>/{{cookiecutter.project_slug}}/` | 必需。包含生成项目。 | Cookiecutter 渲染测试。 |
| 生成项目的 `pyproject.toml` | 内置 Python 模板必需。项目名不能为空，依赖列表必须有效。 | `test_template_renders_without_unrendered_jinja`。 |
| 生成项目的 `.agentseek/lifecycle.toml` | 必需。声明模板身份和本地生命周期行为。 | 渲染测试和生命周期 smoke 测试。 |
| 生成项目的 `.env.example` | 当运行时从环境变量读取配置时必需。 | 生成 README 和生命周期声明。 |
| 生成项目的 `README.md` | 必需。给出从配置到首次成功运行的完整路径。 | 渲染检查和模板 smoke 验证。 |

## 注册表

| 字段 | 要求 |
| --- | --- |
| Key | 使用 `type/name`，并与模板目录和生命周期中的 `template` 值一致。 |
| 描述 | 用一句话说明生成应用及其主要差异。 |
| 唯一来源 | `templates/index.json`。除隔离模板外，每个 Cookiecutter 模板都必须注册。 |
| 新类型 | 必须单独评审 CLI 和测试；只新增目录不够。 |

## 模型服务配置

| 变量 | 何时需要 | 规范 |
| --- | --- | --- |
| `AGENTSEEK_MODEL` | 模板选择托管聊天模型时。 | 模板面向用户的主要模型配置。可以兼容旧别名。 |
| `AGENTSEEK_API_KEY` | 单个 OpenAI-compatible 凭证可以配置运行时时。 | 主要通用凭证。运行时代码可以把它适配到 SDK 变量。 |
| `AGENTSEEK_API_BASE` | 支持自定义 OpenAI-compatible endpoint 时。 | 主要通用 endpoint 配置。留空表示使用提供方默认值。 |
| `AGENTSEEK_MODEL_PROVIDER` | 支持多个原生模型提供方时。 | 选择 provider adapter，模型值必须与所选 provider 匹配。 |
| Provider 原生密钥 | 所选 SDK 要求独立凭证时，例如 `ANTHROPIC_API_KEY` 或 `GOOGLE_API_KEY`。 | 可以按需提供。`.env.example`、生命周期检查、运行时代码和 README 必须使用相同名称和优先级。 |

只要概念适用，公开的模板配置统一使用 `AGENTSEEK_*`。框架原生变量只作为 adapter 或兼容别名，不能形成第二套未记录的配置方式。

## 生命周期声明

| 区块 | 要求 |
| --- | --- |
| 根字段 | `version = 1`、准确的 `template = "type/name"`、可读的 `name`；声明环境检查时使用 `env_file = ".env"`。 |
| `[tools]` | setup 或本地开发前必需的所有可执行文件。 |
| `[paths]` | `agentseek doctor` 需要检查的生成文件或安装目录。 |
| `[env.<name>]` | `agentseek doctor` 需要检查的配置。别名必须与运行时代码一致。 |
| `[services.<name>]` | `agentseek info` 展示的所有稳定用户入口。 |
| `[processes.<name>]` | `agentseek dev` 启动的所有长时间运行进程。至少需要一个进程。 |
| `[checks.<name>]` | 对每个具有稳定健康检查或应用 endpoint 的服务声明 HTTP readiness check。 |
| `[tasks.<name>]` | 通过 `agentseek task` 暴露的一次性 setup、准备或维护动作。每个 task 都必须有描述。 |

生命周期检查的环境变量优先级：

```text
lifecycle default < env_file < shell environment
```

生命周期默认值和 `.env` 只用于检查就绪状态。AgentSeek 不会把它们注入子进程，process command 必须自行加载运行环境。

## Task 命名

| Task | 要求 |
| --- | --- |
| `sync` | 当项目需要单独安装 Python 或 backend 依赖时使用。新模板统一使用 `sync`，不要使用 `backend` 等框架专属名称。 |
| `frontend` | 项目存在独立 frontend 依赖树时，用于安装 frontend 依赖。 |
| `models` | 本地开发前需要下载或转换模型文件时使用。 |
| `<service>` | 准备或启动无法完全由 `agentseek dev` 管理的可选依赖，例如 `seekdb`。 |
| `ingest-sample` | 模板包含 ingestion 流程时，用于导入可重复验证的示例内容。 |
| `<integration>-skills` | 安装可选外部 skill pack。该 task 必须能通过 `agentseek task --list` 发现。 |

生成 README 统一通过 `agentseek task <name>` 引导 setup。原始包管理命令可以解释实现，但不能成为另一条主要使用路径。

## 本地服务和网络

| 能力 | 要求 |
| --- | --- |
| 开发环境 | `agentseek dev` 启动文档所需的所有长时间运行进程。 |
| 默认绑定 | Backend 和 frontend server 默认绑定 loopback。 |
| 远程开发 | 支持远程访问时，必须提供并说明 host override。 |
| 浏览器 API URL | Frontend 根据浏览器地址推导 backend host，或接受显式 public API URL。不能为远程客户端写死 loopback backend。 |
| 无 frontend | 纯 backend 模板必须明确说明不提供 frontend，并指出支持的入口。 |

## 可选能力

| 能力 | 必须说明的内容 |
| --- | --- |
| 知识库 | 说明 ingestion 通过本地文件、server endpoint、UI 还是 lifecycle task 完成，并提供一个可用示例。 |
| 可观测性 | 说明是否支持 tracing、如何开启，以及发送到哪个 backend。不能暗示所有模板都支持 LangSmith。 |
| 本地模型 | 说明模型文件准备方式、支持的 device 配置，以及用于准备模型的 lifecycle task。 |
| 对话语言 | 除非有明确产品要求，默认 prompt 包含 `Answer in the same language as the user's question.`。 |

## README 规范

| 文档 | 必需内容 |
| --- | --- |
| 模板根目录 README | 用途、架构摘要、Cookiecutter 参数、生成目录结构和面向贡献者的实现说明。 |
| 生成项目 README | 前置条件、`.env` 配置、按顺序排列的 lifecycle tasks、`agentseek doctor`、`agentseek dev`、服务入口、可选能力，以及支持时的远程绑定。 |
| 缺失能力 | 对常见但未提供的能力作出明确说明，例如 frontend 或可观测性。 |
| 例外 | 只有存在例外时才添加 `Deviations from the template contract`，并说明规则、原因、用户影响和替代验证。 |

## 例外

| 要求 | 规范 |
| --- | --- |
| 理由 | 必须来自框架或运行时约束，不能只是贡献者偏好。 |
| 文档 | 在生成 README 中记录偏离项。 |
| Pull request | PR 描述中重复说明偏离项及其用户影响。 |
| 验证 | 用测试或 smoke check 证明替代方案可用。 |

## 验证

| 检查 | 命令或依据 |
| --- | --- |
| 注册表一致性 | `uv run python -m pytest tests/cli_commands/test_templates_registry.py -q` |
| 默认渲染和生命周期 smoke | `uv run python -m pytest tests/cli_commands/test_templates_render.py -q` |
| 生成项目检查 | 使用 `agentseek create <absolute-template-path> --no-input` 渲染本地模板。 |
| 文档 | `make docs-test` |

## 相关页面

- [创建模板](../guides/create-template.md)
- [生命周期规范](lifecycle-spec.md)
- [模板](templates.md)
