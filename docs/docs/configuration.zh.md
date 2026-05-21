# 配置

这一页是 agentseek 内置配置层的参考文档。若你想按步骤完成设置，请先看 [快速开始](getting-started.md)。

示例全部使用 `AGENTSEEK_*` 命名，因为这是这个发行版面向项目的变量前缀。兼容 Bub 的 `BUB_*` 仍然完全可用。

各个 contrib package 会在自己的 README 中维护独立配置说明。

## 环境变量命名

agentseek 同时接受 `AGENTSEEK_*` 和 `BUB_*`。

在 agentseek 项目中，优先使用 `AGENTSEEK_*`。启动时，agentseek 会把缺失的 `BUB_*` 从对应的 `AGENTSEEK_*` 里映射出来；如果两者都设置了，则 `BUB_*` 优先。

agentseek 也会读取当前工作目录下的 `.env`。同名配置下，进程环境变量优先于 `.env` 中的值。

## 默认布局

如果没有设置 home 或 project 路径，agentseek 默认使用当前工作区：

```text
.agentseek/
  config.yml
  mcp.json
  agentseek-project/
```

`agentseek install ...` 默认把 `agentseek-project` 当作插件沙箱。若要改成别的目录，请设置 `AGENTSEEK_PROJECT` 或 `BUB_PROJECT`。

## 常用运行时别名

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_MODEL` | 模型标识，例如 `openrouter:free`。 |
| `AGENTSEEK_API_KEY` | 当前模型提供商的 API key。 |
| `AGENTSEEK_API_BASE` | OpenAI-compatible API base URL。 |
| `AGENTSEEK_HOME` | 运行时 home。默认是当前工作区下的 `.agentseek`。 |
| `AGENTSEEK_PROJECT` | `agentseek install` 使用的插件沙箱目录。默认值为 `{AGENTSEEK_HOME}/agentseek-project`，并映射到 `BUB_PROJECT`。 |

## 可选运行时变量

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_MAX_STEPS` | 模型/工具循环的最大步数。 |
| `AGENTSEEK_MAX_TOKENS` | 回复 token 预算。 |
| `AGENTSEEK_MODEL_TIMEOUT_SECONDS` | 模型请求超时。 |

## MCP

`bub-mcp` 默认从 `${BUB_HOME}/mcp.json` 读取 MCP server 定义。按照 agentseek 的默认布局，这个文件就是当前工作区里的 `.agentseek/mcp.json`。

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_MCP_CONFIG_PATH` | Bub MCP 配置路径的别名。当你希望 MCP 配置不放在 `${AGENTSEEK_HOME}/mcp.json`，而是放在项目根目录例如 `.agents/mcp.json` 时，就使用它。 |

在 Docker / Compose 场景下，入口脚本还会额外做一层便利处理：如果挂载工作区里存在 `.agents/mcp.json`，它会自动把这个文件链接到运行时 MCP 配置路径。

## Docker 工作区

下面这些变量主要由 Docker 入口脚本和仓库自带的 Compose 工作流消费。同一个入口脚本也会继续兼容 Bub 别名。

| Variable | Purpose |
| --- | --- |
| `AGENTSEEK_DOCKER_WORKSPACE` | Docker Compose 挂载到 `/workspace` 的宿主机路径。默认是仓库根目录。 |
| `AGENTSEEK_WORKSPACE_PATH` | 容器入口脚本使用的工作区根路径。在仓库自带 Compose 配置中默认是 `/workspace`。 |
| `AGENTSEEK_HOME` | 容器内的运行时 home。在默认 Compose 配置下，它默认是 `/workspace/.agentseek`。 |
| `AGENTSEEK_PROJECT` | 容器内的插件沙箱。在默认 Compose 配置下，它默认是 `/workspace/.agentseek/agentseek-project`。 |
| `AGENTSEEK_SKILLS_HOME` | 容器入口脚本使用的 skill 源目录。默认是工作区下的 `.agents/skills`，如果你设置成非默认值，入口脚本会把它再链接回 Bub 扫描的工作区路径。 |
| `AGENTSEEK_MCP_CONFIG_PATH` | MCP 配置源路径。默认 Compose 会把它设成 `/workspace/.agents/mcp.json`。 |

当这些变量没有显式设置时，入口脚本会把 `/workspace` 视为默认工作区根，并使用 `/workspace/.agents/skills` 作为项目 skill 根目录。

如果 `/workspace/startup.sh` 存在，入口脚本会执行它。否则默认启动 `agentseek gateway`。

## Onboarding

```bash
uv run agentseek onboard
```

这个命令会把配置写入当前生效的 agentseek home；在默认布局下，就是当前工作区中的 `.agentseek/config.yml`。

已安装的 Bub 插件可以在 onboarding 流程里补充自己的提问，并写入各自的配置段。

## Contrib 配置

各个 contrib 集成的配置说明分别维护在自己的 package 文档中：

- [agentseek-observability](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-observability)：运行时追踪链路的 Logfire 和 OTLP 配置。
- [agentseek-tapestore-oceanbase](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-tapestore-oceanbase)：SQLAlchemy tape storage、OceanBase URL 兼容性以及向量设置。
- [agentseek-langchain](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-langchain)：LangChain factory、tool bridge 以及 tape recording 配置。
- [agentseek-schedule-sqlalchemy](https://github.com/ob-labs/agentseek/tree/main/contrib/agentseek-schedule-sqlalchemy)：调度器数据库 URL、表名和回退行为。
