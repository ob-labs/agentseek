---
title: 创建模板
type: how-to
audience: [A2, A3]
runs: yes
verified_on: 2026-07-10
sources:
  - templates/index.json
  - src/agentseek/cli/commands/create.py
  - src/agentseek/cli/lifecycle/spec.py
  - tests/cli_commands/test_templates_registry.py
  - tests/cli_commands/test_templates_render.py
  - "templates/langchain/agentic-rag/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
  - "templates/langchain/markdown-messages/{{cookiecutter.project_slug}}/.env.example"
---

# 创建模板

本指南用于向 `templates/` 贡献内置模板。在确定配置名称和 lifecycle task 前，先阅读[模板编写规范](../reference/template-authoring-contract.md)。

## 前置条件

- 本地已有 AgentSeek checkout，并已安装开发依赖。
- 已明确生成应用的目标，并找到一个运行时相近的现有模板。
- 已选择唯一的 `type/name` spec。除非同时扩展 CLI 的类型支持，否则复用 `bub`、`deepagents` 或 `langchain`。

## 1. 查看最接近的模板

列出公开模板。

```bash
uv run agentseek create --list-templates
```

查看最接近模板的渲染参数。

```bash
uv run agentseek create langchain/agentic-rag --describe
```

只复用新应用需要的结构。框架专属运行时细节保留在生成项目中。

## 2. 创建模板目录

使用以下结构：

```text
templates/<type>/<name>/
  cookiecutter.json
  README.md
  {{cookiecutter.project_slug}}/
    .agentseek/lifecycle.toml
    .env.example
    README.md
    pyproject.toml
```

只有应用确实需要时，才在生成项目目录中添加 application source、frontend 文件、Compose 文件或其他资源。

## 3. 定义渲染参数

`cookiecutter.json` 先包含稳定的身份字段，以及贡献者在渲染时真正需要决定的选项。

```json title="cookiecutter.json 片段"
{
  "project_name": "My Agent",
  "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '_').replace('-', '_') }}",
  "author": "Your Name",
  "system_prompt": "You are a helpful assistant. Answer in the same language as the user's question.",
  "default_model": "openai:gpt-4o-mini"
}
```

只在运行时使用的值放入 `.env.example`，不要把每个环境变量都变成 Cookiecutter prompt。

## 4. 统一模型服务配置

只要概念适用，生成应用的公开配置统一使用 AgentSeek 名称。

```dotenv title=".env.example 片段"
AGENTSEEK_MODEL={{ cookiecutter.default_model }}
AGENTSEEK_API_KEY=
AGENTSEEK_API_BASE=
```

应用在多个原生 provider adapter 之间切换时，增加 `AGENTSEEK_MODEL_PROVIDER`。只有所选 SDK 确实要求时，才增加 provider 专属密钥。文档必须说明运行时代码如何映射别名，以及冲突时谁优先。

在 lifecycle 文件的 `[env.*]` 中声明同一组必需名称。AgentSeek 用这些声明检查就绪状态，不会把 `.env` 注入子进程。

## 5. 定义生命周期

声明生成应用所需的 tools、paths、环境检查、本地服务、长时间运行进程、readiness checks 和 setup tasks。

```toml title=".agentseek/lifecycle.toml 片段"
version = 1
template = "langchain/my-template"
name = "{{ cookiecutter.project_name }}"
env_file = ".env"

[tools]
required = ["uv"]

[env.AGENTSEEK_MODEL]
required = true
default = "{{ cookiecutter.default_model }}"
description = "Chat model used by the generated agent."

[services.backend]
url = "http://127.0.0.1:2024"

[processes.backend]
command = ["uv", "run", "python", "-m", "{{ cookiecutter.project_slug }}.server"]

[checks.backend]
type = "http"
target = "http://127.0.0.1:2024"
timeout = 2
attempts = 3

[tasks.sync]
description = "Install Python dependencies."
command = ["uv", "sync"]
```

Python 或 backend 依赖统一使用 `sync`，独立 frontend 依赖树使用 `frontend`。所有长时间运行的本地进程都放在 `[processes.*]` 下，让 `agentseek dev` 管理文档中的完整开发环境。

Server 默认绑定 loopback。支持远程开发时，增加并说明 host override。浏览器 frontend 必须根据浏览器地址推导 backend host，或接受显式 public API URL。

## 6. 编写两层 README

模板根目录的 `README.md` 包含：

- 生成应用的用途和架构。
- Cookiecutter 参数和默认值。
- 生成目录结构。
- 框架专属的贡献者说明。

生成项目的 `README.md` 包含：

- 前置条件和 `.env` 配置。
- 按顺序排列的 `agentseek task` setup 命令。
- `agentseek doctor`、`agentseek dev` 和服务入口。
- 适用时说明 frontend、知识 ingestion、可观测性、本地模型和远程绑定。
- 明确说明未提供的常见能力，例如无 frontend 或无可观测性集成。

只有框架约束确实要求例外时，才使用 `Deviations from the template contract`。其中必须写明规则、原因、用户影响和替代验证。

## 7. 注册模板

在 `templates/index.json` 中增加一条 `type/name` 记录。

```json title="templates/index.json 片段"
{
  "langchain/my-template": "LangChain example app with AgentSeek lifecycle spec."
}
```

Key 必须与模板目录和 lifecycle 的 `template` 值一致。

## 8. 渲染本地模板

把 spec 设置为需要检查的模板。下面使用仓库内已有模板，因此命令可以直接运行。

```bash
export TEMPLATE_SPEC=langchain/agentic-rag
```

创建空的输出目录。

```bash
export TEMPLATE_OUTPUT="$(mktemp -d)"
```

使用绝对本地路径和 Cookiecutter 默认值渲染。

```bash
uv run agentseek create "$PWD/templates/$TEMPLATE_SPEC" --no-input --output-dir "$TEMPLATE_OUTPUT"
```

检查生成的 `.env.example`、`.agentseek/lifecycle.toml`、README 和应用入口。在生成项目目录中运行 lifecycle commands。

## 9. 运行模板验证

检查注册表覆盖和默认渲染。

```bash
uv run python -m pytest tests/cli_commands/test_templates_registry.py tests/cli_commands/test_templates_render.py -q
```

以 strict mode 构建中英文文档。

```bash
make docs-test
```

如果模板依赖模型转换、外部服务、硬件专属库，或 default render 无法验证的其他集成，则增加有针对性的 CI smoke test。

## 故障排查

| 现象 | 常见原因 | 处理方式 |
| --- | --- | --- |
| 注册表测试报告缺少模板 | `templates/index.json` 没有对应 key。 | 增加准确的 `type/name` 记录，或在注册表测试中记录临时隔离。 |
| 渲染测试在生成文件中发现 `{{` | Cookiecutter 参数缺失或转义错误。 | 在 `cookiecutter.json` 中增加参数，或修正生成文件表达式。 |
| `agentseek doctor` 接受配置，但进程无法读取 | Lifecycle 检查和 runtime loader 使用了不同名称，或进程没有加载 `.env`。 | 对齐名称，并在生成应用中加载运行时配置。 |
| Frontend 本地可用，但远程浏览器访问失败 | Server 或 frontend API URL 写死为 loopback。 | 保留 loopback 默认值，并增加显式 host/API override。 |

## 相关页面

- [模板编写规范](../reference/template-authoring-contract.md)
- [生命周期规范](../reference/lifecycle-spec.md)
- [运行项目任务](run-project-tasks.md)
