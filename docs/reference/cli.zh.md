---
title: CLI 参考
type: reference
audience: [A1, A2, A3, A4]
runs: yes
verified_on: 2026-05-29
sources:
  - src/agentseek/cli.py
  - src/agentseek/__main__.py
  - contrib/agentseek-cli/src/agentseek_cli/standalone.py
  - contrib/agentseek-cli/src/agentseek_cli/plugin.py
  - contrib/agentseek-cli/src/agentseek_cli/app.py
  - pyproject.toml
  - contrib/agentseek-cli/pyproject.toml
---

# CLI 参考

两个 PyPI 包都注册了同名的 console script `agentseek`。你看到的命令面，取决于
当前环境里哪一个是活跃的。

| 源包 | `agentseek` 解析到 | 何时看到它 |
| --- | --- | --- |
| `agentseek-cli`（项目生命周期 CLI） | `agentseek_cli.standalone:app`（`contrib/agentseek-cli/pyproject.toml:18`） | 路径 A —— `uv tool install agentseek-cli` |
| `agentseek`（harness） | `agentseek.__main__:app`（`pyproject.toml:49`） | 路径 B —— `git clone … && uv sync && uv run agentseek` |

`agentseek_cli.standalone:app`（`contrib/agentseek-cli/src/agentseek_cli/standalone.py:24-32`）
在每次调用时惰性解析：

- 如果 **harness**（`agentseek`）**无法**被导入，它会调用
  `agentseek_cli.app.build_app()`，只暴露项目生命周期组。
- 如果 harness **可以**被导入，它会让位给
  `agentseek.__main__.create_cli_app()`。该函数会启动 `BubFramework` 并加载
  所有 Bub plugin —— 包括 `agentseek_cli.plugin:main` —— 因此无论你是从
  `agentseek` 还是 `agentseek-cli` 启动脚本，最终的 CLI 表面是一致的。

`contrib/agentseek-cli/src/agentseek_cli/plugin.py:28-42` 中的 Bub plugin 会
把每一个项目生命周期组挂到 framework app 上，并允许**覆盖**框架内置的 `run`
（Bub 的单条消息分发）为项目生命周期 CLI 的 `run`（本地启动项目）。该覆盖
只在 `agentseek-cli` 与 harness 同时存在时发生。

本页列出每一个子命令，并标注它属于哪一面。

## 项目生命周期命令

这些命令来自 `agentseek-cli`
（`contrib/agentseek-cli/src/agentseek_cli/app.py:22-30`）。它们在**路径 A**
开箱可用；在**路径 B**下，只要 harness 环境里装了 `agentseek-cli`
（例如通过 `uv sync --extra cli`，或者生成的项目本身依赖它），它们也会出现。

### `agentseek create [SPEC]`

:   从预构建的模板（位于 `templates/` 下的 cookiecutter）创建一个新的 agent project。

    | 参数 / 标志 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `spec` | TEXT | — | 框架类型（`deepagents`、`langchain`、`bub`）、`type/name`、git URL，或本地路径。 |
    | `--template` | TEXT | — | 所选类型下的具名模板（例如 `cli-remote`）。 |
    | `--checkout` | TEXT | — | 远程拉取的 branch / tag / commit。 |
    | `--list-templates` | flag | — | 列出该类型可用的模板并退出。 |
    | `--no-input` | flag | off | 跳过 cookiecutter 的交互提示。 |

    捆绑模板列表请参见 [Templates reference](templates.md)。

### `agentseek run`

:   完成 `.env` 配置后，在本地启动项目。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--port` | INTEGER | `.env` 中的 `$PORT`，否则为 `3000` | 前端端口。 |
    | `--host` | TEXT | `127.0.0.1` | 探测就绪状态的主机。 |
    | `--no-browser` | flag | off | 跳过打开默认浏览器。 |
    | `--wait-timeout` | INTEGER | `30` | 等待前端的秒数。 |
    | `--mode` | `auto\|compose\|python` | `auto` | 启动模式覆盖。 |

    在**路径 B 且未装 `agentseek-cli`** 的情况下，上游 Bub 内置的
    `run MESSAGE`（单条入站消息）会以同名暴露作为兜底。plugin 的覆盖
    （`CLI_OVERRIDE_NAMES = {"run"}`）仅在 `agentseek-cli` 存在时发生。

### `agentseek build`

:   将 project 构建为容器镜像（封装 `docker build` / `docker buildx build`）。
    顶层命令 — 尽管 `--help` 中出现了 `COMMAND [ARGS]...` 这一行，但它没有子命令。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--tag`, `-t` | TEXT | `<cwd-slug>:latest` | 镜像 tag。 |
    | `--file`, `-f` | PATH | （由 `agentseek-cli` 解析） | Dockerfile 的路径。 |
    | `--context` | PATH | `.` | 构建上下文目录。 |
    | `--platform` | TEXT | — | 以逗号分隔的目标平台。 |
    | `--push` | flag | off | 构建成功后推送。 |
    | `--no-cache` | flag | off | 构建时不使用缓存。 |
    | `--build-arg` | TEXT (repeatable) | — | `KEY=VALUE` 形式的构建时变量。 |
    | `--dry-run` | flag | off | 打印解析后的命令而不执行。 |

### `agentseek deploy`

:   生成部署清单（docker-compose / k8s）。顶层命令 — 尽管 `--help` 中出现了
    `COMMAND [ARGS]...` 这一行，但它没有子命令。在 v1 中，`--dry-run` 是必填的。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--dry-run` | flag | v1 中必填 | 生成清单但不部署。 |
    | `--mode` | `docker-compose\|k8s\|both` | `both` | 部署目标。 |
    | `--output` | DIRECTORY | `deploy` | 清单写入位置。 |
    | `--image` | TEXT | `<project-slug>:latest` | 容器镜像引用。 |
    | `--slug` | TEXT | 从 cwd 推断 | 用于 service / deployment 名称的 project slug。 |
    | `--port` | INTEGER | `8000` | 服务端口。 |
    | `--replicas` | INTEGER (≥1) | `1` | k8s Deployment 副本数。 |
    | `--namespace` | TEXT | `default` | k8s namespace。 |

### `agentseek api`

:   当安装了 `agentseek-api` 时，将 API 运行时命令转发给它。若环境中没有
    `agentseek-api`，所有子命令都会失败并提示：

    ```text title="output"
    The `agentseek api` commands require `agentseek-api` in the current environment.
    Install it first, for example: `uv pip install -e references/agentseek-api`.
    ```

    子命令（每个都将同名命令转发给 `agentseek-api`）：
    `dev`、`serve`、`dockerfile`、`build`、`up`、`version`。

### `agentseek ctx`

:   ContextSeek — 语义上下文层。转发给 `contextseek` CLI。当
    `agentseek-contextseek` 在 path 上时可用（例如在路径 B 上通过
    `uv sync --extra context`，或在路径 A 上由生成项目拉入）。

    子命令包括 `add`、`retrieve`、`expand`、`compact`、
    `forget`、`delete`、`overview`、`tools`、`metrics`、`dream`、`feedback`、
    `upstream`、`evidence-chain`、`chain-confidence`、`skill-tools`、
    `skill-context`、`skill-import`、`items`。

    用法参见 [How to use ContextSeek](../how-to/use-contextseek.md) 以及
    [contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md)。

### `agentseek skills`

:   通过上游 `vercel-labs/skills` CLI 管理 agent skills（使用 `npx` 运行）。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--dir` | PATH | `$PWD` | 运行 `skills` 的 workspace 目录。 |

    子命令（每个都转发给 `npx skills`）：`add`、`list`、`find`、
    `update`、`remove`、`init`。

## Harness 运行时命令

这些命令来自 harness（`agentseek`），只在**路径 B**下可用（或在生成项目里
`uv sync` 之后可用）。仅 `uv tool install agentseek-cli` 不会带入它们。

### 顶层选项

```text
Usage: agentseek [OPTIONS] COMMAND [ARGS]...
```

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `--workspace`, `-w` | TEXT | (unset) | workspace 的路径。 |
| `--help` | flag | — | 显示顶层帮助并退出。 |

### `agentseek chat`

:   通过 CLI channel 使用 Bub 内置的 chat；agentseek 增加了 lifecycle channels
    （`src/agentseek/cli.py:83`）。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--chat-id` | TEXT | `local` | Chat id。 |
    | `--session-id` | TEXT | `None` | 可选的 session id。 |

### `agentseek onboard`

:   交互式收集 plugin 配置并写入 Bub 的配置文件。使用 `src/agentseek/cli.py:23`
    中的 agentseek 品牌横幅。

    除 `--help` 外不接收其他参数。

### `agentseek gateway`

:   启动消息监听器（例如 telegram）。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--enable-channel` | TEXT (repeatable) | all | 要为 CLI 启用的 channels（默认：all）。 |

### `agentseek install [SPECS]...`

:   将 plugin 安装到 Bub 的环境中，或者在没有提供规格时同步环境。agentseek 将安装
    sandbox 替换为 `DEFAULT_PLUGIN_SANDBOX = "agentseek-project"`
    （`src/agentseek/cli.py:115`、`src/agentseek/env.py:22`）。

    | 参数 / 标志 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `SPECS` | TEXT… | `[]` | Git URL、`owner/repo`，或 bub-contrib 中的 `name@branch`。 |
    | `--project` | PATH | `${BUB_PROJECT}`（默认为 `${BUB_HOME}/agentseek-project`） | project 目录的路径。 |

    帮助文本仍打印上游默认值 `~/.bub/bub-project`。运行时默认值是 agentseek sandbox，
    因为 `apply_agentseek_env_aliases` 在 Typer 读取默认值之前就设置了 `BUB_PROJECT`
    （`src/agentseek/env.py:73`）。

### `agentseek uninstall PACKAGES...`

:   从 Bub 的环境中卸载 plugin。`PACKAGES` 是必填项。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--project` | PATH | `${BUB_PROJECT}` | project 目录的路径。 |

### `agentseek update [PACKAGES]...`

:   更新指定的包，或在未提供参数时更新 Bub 环境中的所有包。

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--project` | PATH | `${BUB_PROJECT}` | project 目录的路径。 |

### `agentseek mcp`

:   管理已解析到的 `mcp.json` 中的 MCP server（路径由 `bub-mcp` 从
    `${BUB_MCP_CONFIG_PATH}` / `${AGENTSEEK_MCP_CONFIG_PATH}` 解析，
    默认为 `${BUB_HOME}/mcp.json`）。

    子命令：`list`、`add`、`remove`。

    `agentseek mcp list` —— 列出已注册的 MCP 工具。除 `--help` 外没有其他参数。

    `agentseek mcp add NAME TARGET...` 的参数：

    | 参数 / 标志 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `NAME` | TEXT | — | server 名称（必填）。 |
    | `TARGET` | TARGET… | — | 远端 server 的 URL，或 stdio 形式的 `-- <command>`（必填）。 |
    | `--transport` | `http\|sse\|stdio` | — | MCP transport（必填）。 |
    | `--env` | TEXT（可重复） | — | stdio server 使用的 `KEY=VALUE` 环境变量。 |
    | `--header` | TEXT（可重复） | — | http 或 sse server 使用的 `Name: Value` 请求头。 |

    `agentseek mcp remove NAME` —— 按名称删除 server。`NAME` 必填，
    没有其他参数。

    端到端流程见 [How to configure MCP servers](../how-to/configure-mcp.md) 与
    [How to add an MCP server](../how-to/add-mcp-server.md)。

### `agentseek login`

:   认证命令。

    子命令：`openai` — 使用 OpenAI OAuth 登录。

    `agentseek login openai` 的参数：

    | 参数 | 类型 | 默认值 | 描述 |
    | --- | --- | --- | --- |
    | `--codex-home` | PATH | — | 存储 Codex OAuth 凭证的目录。 |
    | `--browser` / `--no-browser` | flag | `--browser` | 在浏览器中打开 OAuth URL。 |
    | `--manual` | flag | off | 粘贴 callback URL 或 code，而不是等待本地回调服务器。 |
    | `--timeout` | FLOAT | `300.0` | OAuth 等待超时（秒）。 |

## 实际执行的 help 命令

以下命令是从仓库根目录（路径 B，启用所有 extras）运行以填充本页内容的：

```bash
uv run agentseek --help
uv run agentseek run --help
uv run agentseek chat --help
uv run agentseek onboard --help
uv run agentseek gateway --help
uv run agentseek install --help
uv run agentseek uninstall --help
uv run agentseek update --help
uv run agentseek create --help
uv run agentseek build --help
uv run agentseek deploy --help
uv run agentseek api --help
uv run agentseek api dev --help
uv run agentseek ctx --help
uv run agentseek skills --help
uv run agentseek skills add --help
uv run agentseek mcp --help
uv run agentseek mcp list --help
uv run agentseek mcp add --help
uv run agentseek mcp remove --help
uv run agentseek login --help
uv run agentseek login openai --help
```

## 另请参阅

- 概览：[agentseek](../index.zh.md)
- 概念解释：[选择一个入口](../explanation/choosing-an-entry-point.zh.md)
- 操作指南：[How to install a plugin](../how-to/install-a-plugin.md)、[How to run agentseek locally](../how-to/run-locally.md)、
  [How to run the gateway](../how-to/run-gateway.md)、[How to build and deploy](../how-to/build-and-deploy.md)
- 参考：[Environment variables reference](environment.md)、[Packages reference](packages.md)
