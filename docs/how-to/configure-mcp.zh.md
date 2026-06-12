---
title: 如何配置 MCP 服务器
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/env.py
  - entrypoint.sh
  - pyproject.toml
---

# 如何配置 MCP 服务器

当你要让 AgentSeek 调用 MCP server 暴露的工具时使用本页。

## 前置条件

- 项目环境中已安装 `bub-mcp`。
- 至少有一个能在同一环境中运行的 MCP server。

```bash
uv add bub-mcp
```

## 步骤

1. 在项目中创建 `.agents/mcp.json`。

   ```json title=".agents/mcp.json"
   {
     "mcpServers": {
       "local-tools": {
         "command": "python",
         "args": ["-m", "my_package.mcp_server"],
         "env": {
           "LOG_LEVEL": "info"
         }
       },
       "github": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-github"],
         "env": {
           "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_fake_replace_me"
         }
       }
     }
   }
   ```

2. 让 AgentSeek 读取该文件。

   ```bash title=".env"
   AGENTSEEK_MCP_CONFIG_PATH=.agents/mcp.json
   ```

3. 重启 runtime。

   ```bash
   uv run agentseek chat
   ```

在 Docker Compose 默认配置中，该路径已经是 `/workspace/.agents/mcp.json`。

### CLI 快捷方式

当当前 CLI 环境已安装 `bub-mcp` 时，`agentseek mcp` 可以编辑同一个配置文件。

```bash
uv run agentseek mcp list
```

```text title="output"
No MCP tools registered.
```

```bash
uv run agentseek mcp add github https://example.com/mcp \
  --transport http --header "Authorization: Bearer $TOKEN"
```

```bash
uv run agentseek mcp add local-tools --transport stdio \
  --env LOG_LEVEL=info -- python -m my_package.mcp_server
```

如果用自定义路径，先创建父目录再运行 `mcp add`。

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| `No such command 'mcp'` | 未安装 `bub-mcp`。 | 将 `bub-mcp` 加入项目依赖。 |
| 工具缺失 | server 命令启动失败。 | 在 AgentSeek 之外运行该 server 命令。 |
| 鉴权失败 | `env` 中缺少 token。 | 在对应 server 条目下添加凭据。 |
| 修改没有生效 | runtime 在编辑前已经启动。 | 重启 `agentseek chat` 或 `agentseek gateway`。 |

## 回退

从 `mcp.json` 中移除 server 条目。如果设置过 `AGENTSEEK_MCP_CONFIG_PATH`，
取消设置。

## 相关

- 参考：[环境变量](../reference/environment.zh.md)
- Docker：[如何使用 Docker Compose 运行](run-with-docker-compose.zh.md)
