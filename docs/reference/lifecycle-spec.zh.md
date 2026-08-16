---
title: 生命周期规范
type: reference
audience: [A2]
runs: no
verified_on: 2026-08-17
sources:
  - src/agentseek/cli/lifecycle/spec.py
  - src/agentseek/cli/lifecycle/environment.py
  - src/agentseek/cli/lifecycle/dotenv_adapter.py
  - src/agentseek/cli/lifecycle/compatibility.py
  - src/agentseek/cli/lifecycle/core.py
  - src/agentseek/cli/commands/dev.py
  - src/agentseek/cli/commands/doctor.py
  - src/agentseek/cli/commands/info.py
  - src/agentseek/cli/lifecycle/authored.py
  - src/agentseek/cli/lifecycle/normalize.py
  - src/agentseek/cli/lifecycle/json_output.py
  - src/agentseek/cli/lifecycle/safety.py
  - specs/lifecycle-v2-service-discovery.md
  - docs/adr/0001-versioned-template-catalog-boundary.md
  - templates/index.json
  - tests/cli_commands/test_templates_render.py
  - "templates/bub/default/{{cookiecutter.project_slug}}/.agentseek/lifecycle.toml"
---

# 生命周期规范

## 文件

AgentSeek 从当前目录向上查找生命周期规范：

```text
.agentseek/lifecycle.toml
```

其他项目文件不参与生命周期发现。

## 编写版本与 catalog 边界

AgentSeek 当前加载并验证编写的生命周期版本 `1` 和 `2`。现有的人工使用命令及其 v1
行为保持兼容。

| 编写版本或位置 | 当前边界 |
| --- | --- |
| `1`, `2` | 编写的生命周期文件会被加载和验证。 |
| `templates/` | core 仍是 `version = 1` 兼容镜像。 |
| `agentseek-ai/agentseek-templates` | 锁定的独立 `v0.1.0` catalog 为新项目提供 `version = 2` 模板。 |
| 规范化与机器接口 | V1 和 v2 都投影到同一个安全规范化模型；`info --json` 和 `doctor --json` 提供公共 schema 版本 `1`。 |

完整的编写契约见已发布的 [lifecycle v2 概览
(`lifecycle-v2-service-discovery.md`)](lifecycle-v2-service-discovery.md)。
精确的规范源地址为
<https://github.com/ob-labs/agentseek/blob/main/specs/lifecycle-v2-service-discovery.md>。

## 生命周期 v1 形状

```toml
version = 1
template = "bub/default"
name = "My Bub Agent"
env_file = ".env"

[tools]
required = ["uv", "node", "npm"]

[paths]
required = ["frontend/package.json", "frontend/node_modules"]

[env.BUB_MODEL]
required = true
default = "openai:gpt-4o-mini"

[env.BUB_API_KEY]
required = true
aliases = ["BUB_OPENAI_API_KEY"]

[services.app]
url = "http://127.0.0.1:5173"

[processes.frontend]
command = ["npm", "run", "dev"]
cwd = "frontend"

[checks.frontend]
type = "http"
target = "http://127.0.0.1:5173"
timeout = 2
attempts = 3

[tasks.frontend]
description = "Install frontend dependencies."
command = ["npm", "install", "--prefix", "frontend"]
```

## 段落

| 段落 | 作用 |
| --- | --- |
| `env_file` | 可选的项目本地 dotenv 文件，仅由非 dry-run 的 `agentseek dev` 解析一次，用于声明的环境检查和长运行子进程。 |
| `tools` | 项目需要的可执行文件。 |
| `paths` | 必需的本地文件或目录。 |
| `env.<name>` | AgentSeek 应检查的环境变量。默认值优先级低于 `env_file` 和 shell 变量。 |
| `services.<name>` | `agentseek info` 展示的公开本地服务端点。 |
| `processes.<name>` | `agentseek dev` 启动的长运行命令。 |
| `checks.<name>` | `agentseek doctor --live` 使用的 HTTP live 就绪检查。2xx 和 3xx 响应成功。 |
| `tasks.<name>` | `agentseek task <name>` 运行的一次性任务。`cwd` 是项目相对路径，且必须存在。 |

生命周期 v2 的 HTTP 检查要求 `timeout` 为大于 `0` 且不超过 `300` 的有限秒数，
`attempts` 为正整数。

## 环境检查

每次非 dry-run 的 `agentseek dev` 调用都会只创建一次不可变快照（immutable snapshot）。
它会先捕获启动环境，再用项目 `env_file` 与已捕获启动环境中的非空值创建该快照：

```text
lifecycle env_file < non-empty captured launch environment
```

受限的 python-dotenv 会按文件中物理绑定出现的顺序解析，
并在文件内没有值时回退到已捕获的启动环境。在生命周期 dotenv 中，`KEY=` 表示一个
存在但为空的赋值；裸 `KEY` 不产生赋值。原始启动值为空时，会在创建快照前省略，因此
dotenv 值可以补上它。

就绪检查、内部预检与每个长运行子进程都使用同一个快照。生命周期默认值可以满足
就绪检查，但绝不会进入快照。只有声明在 `[env.<name>]` 的 key 及其 aliases 会参与
就绪检查。AgentSeek 只保证初始子进程环境/快照：
其中只有已解析的值，不包含源路径、provenance 或要求再次解析的指令。兼容的子进程配置
补全可以填入缺失 key，但不得替换继承的已有 key。任意子进程代码
仍可自行修改其进程环境；禁止重复加载覆盖配置只是模板编写约束，不是 AgentSeek 的
强制保证。`agentseek task` 不继承生命周期 `env_file`，其行为保持不变。

使用 API completion contract 的生命周期进程需要
`agentseek-api >= 0.2.2`。`agentseek dev --dry-run` 只打印计划，不读取生命周期
dotenv。缺失、无法解码或 malformed dotenv 的严格保证只适用于非 dry-run 的
`agentseek dev`：它会在任何子进程启动前返回 `exit 2`，不创建部分快照，且诊断不得
包含值；裸 `KEY` 仍是有效语法。单独运行 `agentseek info` 仍会报告 dotenv 状态，
不会创建快照。单独严格运行 `agentseek doctor --strict` 会渲染
就绪失败（例如 dotenv 缺失），并返回 `exit 1`。

## 生命周期 v1 第一阶段范围

Version 1 支持必需工具、必需路径、项目环境需求、HTTP live 检查、长运行进程和一次性任务。
它不支持可选 tool/path 检查、TCP 检查、进程级环境覆盖或多个 env 文件。生命周期 schema
不新增独立插值模式：配置的 `env_file` 使用受限的 python-dotenv，按文件中物理绑定出现的
顺序解析，并回退到已捕获的启动环境。

## 生命周期 v2 编写字段

V2 保留 v1 的 `tools`、`paths` 与 `env` 段，并仍要求至少声明一个 process。根字段为
`version`、`template` 和 `name`；可选字段为 `description`、`env_file` 与 `guide`；
`template` 和 `name` 必须非空。`guide`、`env_file`、`paths.required` 以及 process/task 的
`cwd` 必须是项目相对路径，且解析后仍受限于项目根目录。

每个 `services.<id>` 条目包含 `name`、`url`、`kind`、`display`、`primary`、
`description`、可选 `tech` 与有类型的 `links`。`kind` 只能是 `web`、`api`、`protocol`、
`database` 或 `other`；`display` 只能是 `default`、`advanced` 或 `hidden`。`display`
只是展示提示：它绝不控制认证、授权、网络暴露或 process 启动。

V2 默认使用同 ID 关系：同名 process 提供 service，同名 check 检查 service。需要显式关系时，
使用 `processes.<id>.provides`、`checks.<id>.service` 以及 `tasks.<id>.starts` 或
`tasks.<id>.stops`。标识符必须符合 v2 标识符语法，引用的每个 service 都必须存在。声明
service 的项目必须恰有一个非隐藏的 `primary = true` service；check 必须有同 ID 或显式
service。验证还会拒绝未知字段、空 command、重复的 `tools.required` 或 `paths.required`
值、不安全的可执行文件名、路径、端点及有类型的引用 URL。

## 公开命令

| 命令 | 行为 |
| --- | --- |
| `agentseek info [--verbose] [--json]` | 打印项目事实，或以 JSON 输出确定且安全的生命周期元数据。 |
| `agentseek doctor [--live] [--strict] [--json]` | 检查 tools、paths、env 和可选 live endpoints；`--json` 不能与 `--strict` 同时使用。 |
| `agentseek dev [--dry-run] [--skip-check]` | 打印或启动声明的开发进程。`--skip-check` 只跳过预先的 strict `doctor` 检查。 |
| `agentseek task --list` | 列出 `tasks` 下声明的任务。 |
| `agentseek task <name>` | 运行一个声明的一次性任务。 |

## 错误

| 条件 | 结果 |
| --- | --- |
| 缺少 `.agentseek/lifecycle.toml` | Exit code `2`。 |
| 生命周期规范版本不支持 | Exit code `2`。 |
| 生命周期规范无效 | Exit code `2`。 |
