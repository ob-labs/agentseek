# 快速开始

这份教程会从全新仓库检出开始，把内置的 agentseek CLI 跑起来，并让生成的运行时状态保留在当前工作区中。

你需要：

- Python 3.12 或更新版本
- `uv`
- 一个可用的模型提供商 API key，用于获得真实模型响应

下面的命令都使用 `uv run agentseek ...`，默认你在仓库根目录执行。

## 1. 克隆并安装

```bash
git clone https://github.com/ob-labs/agentseek.git
cd agentseek
uv sync
uv run agentseek --help
```

`agentseek` 命令是一个兼容 Bub 的 CLI 入口，只是在品牌和默认行为上做了 agentseek 的封装。

## 2. 配置模型

在 agentseek 发行版里，推荐使用 `AGENTSEEK_*` 变量。它们会被透传成 Bub 可识别的 `BUB_*` 别名。

```bash
export AGENTSEEK_MODEL=openrouter:free
export AGENTSEEK_API_KEY=sk-or-v1-your-key
export AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
```

上面的 API key 只是占位符。要得到真实模型响应，你需要替换成有效的 key。

你也可以先复制 `.env.example` 到 `.env` 再进行编辑：

```bash
cp .env.example .env
```

agentseek 会通过自己的 settings 层读取 `.env`，并在缺失 `BUB_*` 时，用同名的 `AGENTSEEK_*` 值补齐。

## 3. 启动聊天会话

```bash
uv run agentseek chat
```

你应该会看到一个交互式聊天会话。用 `Ctrl+C` 停止即可。

也可以直接通过 CLI 跑单次 prompt：

```bash
uv run agentseek run "Summarize this workspace in one sentence."
```

## 4. 查看本地状态

默认情况下，agentseek 会把本地配置和运行时状态存到当前工作区下的 `.agentseek`。

如果你想改位置，可以设置 `AGENTSEEK_HOME` 或 `BUB_HOME`。

主要默认路径如下：

```text
.agentseek/config.yml
.agentseek/mcp.json
.agentseek/agentseek-project
```

`agentseek install ...` 会把 `.agentseek/agentseek-project` 作为 Bub 的插件沙箱，除非你显式设置了 `AGENTSEEK_PROJECT` 或 `BUB_PROJECT`。

## 5. 增加本地 Skills 和 MCP

项目级本地 skill 可以放在：

```text
.agents/skills
```

Bub 会自动从工作区发现这个目录，因此本地 `agentseek` 运行无需额外接线就能使用这些 skill。

对于 MCP，`bub-mcp` 默认读取 `${BUB_HOME}/mcp.json`。在 agentseek 的默认布局下，也就是：

```text
.agentseek/mcp.json
```

如果你更想把 MCP 文件放到项目根目录，比如 `.agents/mcp.json`，可以在启动 CLI 前显式设置 `AGENTSEEK_MCP_CONFIG_PATH`。

```bash
export AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json
uv run agentseek chat
```

## 6. Docker Compose

如果你想把 `agentseek` 放进容器运行，并挂载当前工作区，仓库已经自带 `docker-compose.yml`：

```bash
cp .env.example .env
make compose-up
```

这个模式会把当前仓库挂载到 `/workspace`，因此容器会直接复用宿主机上的这些路径：

- `.agents/skills`
- `.agents/mcp.json`
- `.agentseek`
- 可选的 `startup.sh`

它会自动发现 `.agents/mcp.json`，并把它链接到容器内运行时 MCP 配置路径。
如果你要使用其他 MCP 配置文件，设置 `AGENTSEEK_MCP_CONFIG_PATH` 即可。

如果挂载的工作区里存在 `startup.sh`，入口脚本会执行它。否则默认启动：

```bash
agentseek gateway
```

如果你希望 Compose 挂载另一个宿主机目录到 `/workspace`，请设置 `AGENTSEEK_DOCKER_WORKSPACE`。

## 7. 验证仓库

本地开发时，建议先跑这几组基础检查：

```bash
make check
make test
make docs-test
```

## 下一步

- 运行 `uv run agentseek onboard`，以交互方式把配置写入 `.agentseek/config.yml`。
- 如果你想直接使用上游 Bub CLI，可以执行 `uv run bub ...`。
- 环境变量别名、本地路径和 Docker 设置详见 [配置](configuration.md)。
- 如果你要增加项目指令、skill、MCP 配置或 Bub 兼容插件，请看 [扩展](extensions.md)。
- 想查看 contrib 能力，请从 [总览](index.md) 跳到各个 package README。
