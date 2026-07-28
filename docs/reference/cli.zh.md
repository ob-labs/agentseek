---
title: CLI 参考
type: reference
audience: [A2]
runs: no
verified_on: 2026-07-28
sources:
  - pyproject.toml
  - src/agentseek/__main__.py
  - src/agentseek/cli/catalog.py
  - src/agentseek/cli/runtime.py
  - src/agentseek/cli/commands/create.py
  - src/agentseek/cli/commands/dev.py
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/commands/info.py
  - src/agentseek/cli/commands/task.py
  - src/agentseek/data/catalog-lock.json
---

# CLI 参考

## 安装和调用

| 命令 | 说明 |
| --- | --- |
| `uv tool install agentseek` | 安装日常使用的 CLI。 |
| `agentseek ...` | 安装后运行生命周期命令。 |
| `uvx agentseek ...` | 不安装工具，只运行一次 AgentSeek 命令。 |

## 根选项

| 选项 | 说明 |
| --- | --- |
| `--mode [cli\|agent]` | 选择 CLI profile。当前文档化的生命周期工作流使用 `cli`。 |
| `--help` | 显示所选 profile 的帮助。 |

## 默认命令

| 命令 | 说明 |
| --- | --- |
| `agentseek create [spec]` | 从模板创建项目。 |
| `agentseek doctor` | 通过生命周期规范检查本地就绪状态。 |
| `agentseek dev` | 通过生命周期规范启动本地开发。 |
| `agentseek info` | 显示项目元数据和入口。 |
| `agentseek task` | 运行项目定义的生命周期规范任务。 |
| `agentseek version` | 显示 AgentSeek 版本信息。 |

## `create`

### 形式

| 形式 | 说明 |
| --- | --- |
| `agentseek create` | 交互式选择类型和模板。 |
| `agentseek create <type>` | 使用该类型的默认模板。 |
| `agentseek create <type>/<name>` | 使用指定模板。 |
| `agentseek create <url-or-absolute-path>` | 把 spec 直接传给 Cookiecutter。 |

内置模板类型集合当前是 `bub`、`deepagents` 和 `langchain`。

### 选项

| 选项 | 说明 |
| --- | --- |
| `spec` | 模板类型、`type/name`、Git URL 或绝对本地路径。 |
| `--list-templates` | 列出模板。带 `type` 时只列出该类型。 |
| `--filter keyword` | 按模板 spec 或描述过滤列出的模板。 |
| `--template name` | 选择所选类型下的命名模板，例如 `bub --template default`。 |
| `--template` | 列出模板的兼容入口。新脚本优先使用 `--list-templates`。 |
| `--template-repo <https-url>` | 选择包含 `templates/index.json` 的显式 AgentSeek 模板目录仓库。必须同时提供 40 个小写字符的 commit SHA 作为 `--checkout`。不能与位置参数中的直接 Cookiecutter URL 或绝对路径组合使用。 |
| `--checkout ref` | 对直接 Cookiecutter 源，可使用分支、tag 或 commit。与 `--template-repo` 一起使用时，值必须匹配 `[0-9a-f]{40}`。 |
| `--output-dir path` | 将生成项目写入所选目录下。默认使用当前工作目录。 |
| `--no-input` | 跳过 Cookiecutter 变量提示，使用模板默认值。 |
| `--describe` | 打印模板描述和 Cookiecutter 变量，不生成项目。 |

### 模板目录源规则

`--checkout` 有三种不同模式：

| 模式 | `--checkout` 行为 |
| --- | --- |
| 直接 Cookiecutter 源 | 将分支、tag 或 commit 与位置参数 URL/路径、可选模板目录一起原样传给 Cookiecutter。 |
| 命名/默认 AgentSeek 模板目录 | 不带 `--template-repo` 时默认使用 wheel 内嵌的目录锁。可选 ref 是独立目录仓库的显式开发覆盖值；不会自动选择 core 中的本地 v1 镜像。 |
| 显式 AgentSeek 模板目录覆盖 | 带 `--template-repo` 时必须提供精确的 40 位小写 commit SHA。列出、过滤、描述和创建都使用这个不可变坐标。 |

| 输入 | 解析规则 |
| --- | --- |
| 不带 `--template-repo` 的列表、过滤或交互选择 | 读取已安装 wheel 内嵌的注册表快照，不需要网络请求。 |
| 不带 `--template-repo` 的命名模板或描述 | 只获取或复用内嵌不可变目录锁记录的模板。 |
| 带 `--template-repo` 和有效不可变 `--checkout` 的命名模板、列表、过滤或描述 | 所有操作使用同一个显式模板目录仓库及 commit。 |
| 位置参数 URL 或绝对路径 | 直接传给 Cookiecutter，不改变原有的 URL/路径行为。 |
| `--template-repo` 与位置参数中的直接 Cookiecutter URL 或绝对路径组合 | 拒绝这两个冲突的来源。 |
| 显式模板目录的仓库、checkout、注册表或模板失败 | 返回错误；不回退到内置模板或本地 checkout。 |

显式模板目录缓存以规范化仓库 URL 和精确 commit 为键，复用前必须验证
匹配的缓存元数据。内置锁定目录的缓存复用还要求模板内容与安装 wheel
中的可信摘要一致。

AgentSeek 0.1.0 将默认目录锁定到
[`agentseek-ai/agentseek-templates` v0.1.0](https://github.com/agentseek-ai/agentseek-templates/releases/tag/v0.1.0)
的 commit `494863bc1b9aab19f9885d716c03ce654fb26014`。生成项目的依赖则独立锁定到
core 快照 `core-snapshot-v0.1.0` 的
`883addad1e2993c4be6fc8ba053f87f25fb5057a`。下载或验证失败会直接报错；
CLI 不会回退到可变的 `main`、core 中的本地 v1 镜像或其他目录版本。

`--list-templates`、`--filter` 和 `--describe` 仅检查模板目录内容，不执行
Cookiecutter hooks。生成操作信任所选模板内容，可能执行其 Cookiecutter
hooks。生成项目中的 `_agentseek_source_url` 始终指向 AgentSeek 核心仓库，
不指向模板目录仓库。

### 缺失模板

| 形式 | 行为 |
| --- | --- |
| `agentseek create bub --template missing` | 以代码 `2` 退出，并显示缺失模板和支持的 `bub` 模板。 |
| `agentseek create bub/missing` | 以代码 `2` 退出，并显示缺失模板和支持的 `bub` 模板。 |

## `doctor`

| 选项 | 说明 |
| --- | --- |
| `--live` | 检查已经运行的本地服务。 |
| `--strict` | 把警告视为失败。 |
| `--json` | 输出一个带 schema 版本的 JSON 文档，包含静态及可选实时诊断结果。 |

`--strict` 与 `--json` 不能同时使用。在 JSON 模式中，即使检查失败，已完成的
doctor 运行仍使用 `ok: true`；诊断结果由 `data.passed` 和进程退出码表达。
受控 JSON 输出只写入 stdout。

## `dev`

| 选项 | 说明 |
| --- | --- |
| `--dry-run` | 打印启动计划，不启动服务。 |
| `--skip-check` | 启动前跳过预先的 strict `doctor` 检查。核心必需输入仍会检查。 |

## `info`

| 选项 | 说明 |
| --- | --- |
| `--verbose` | 显示生命周期 loader 发现细节。 |
| `--json` | 输出一个带 schema 版本的 JSON 文档，包含规范化的项目、服务、检查、任务、参考链接和动作元数据。 |

`info` 会打印当前项目的服务、环境状态、生命周期任务名称和说明，以及下一步命令。

JSON 输出使用公共 schema 版本 `1`，相同规范化输入会得到确定性输出，并排除环境变量值、
原始命令、不安全 URL 和主机绝对路径。生命周期 v1 仍受支持，但会标记
`metadata_complete: false`；生命周期 v2 会给出完整服务拓扑。`--verbose` 与
`--json` 一起使用时不会混入诊断文本。

规范化 DTO、错误、排序和退出码契约见
[Lifecycle v2 服务发现](lifecycle-v2-service-discovery.zh.md)。

## `task`

| 形式 | 说明 |
| --- | --- |
| `agentseek task --list` | 列出项目定义的生命周期规范任务。 |
| `agentseek task --help` | 显示 AgentSeek task 边界。 |
| `agentseek task <name>` | 运行项目定义的生命周期规范任务。 |

`task` 必须从包含 `.agentseek/lifecycle.toml` 的项目目录运行。
