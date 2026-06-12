---
title: 如何使用 ContextSeek
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/cli/runtime.py
  - contrib/agentseek-contextseek/README.md
---

# 如何使用 ContextSeek

当你要让 AgentSeek 使用 ContextSeek 记忆时使用本页。

## 前置条件

- 当前项目中已经安装 AgentSeek。
- 你已经决定 ContextSeek 存储项目数据的位置。

## 步骤

1. 将 ContextSeek 加入项目。

   ```bash
   uv add agentseek-contextseek
   ```

2. 配置 ContextSeek 存储。

   ```bash title=".env"
   AGENTSEEK_CTX_STORAGE_PATH=.contextseek/store
   ```

3. 检查转发的 CLI。

   ```bash
   uv run agentseek ctx --help
   ```

   ```text title="output"
   usage: contextseek [-h]
                      {add,retrieve,expand,compact,forget,delete,overview,tools,metrics,dream,feedback,upstream,evidence-chain,chain-confidence,skill-tools,skill-context,skill-import,items}
                      ...
   ```

4. 添加一条上下文项。

   ```bash
   uv run agentseek ctx add --scope my-scope --text "..."
   ```

5. 检索排序命中。

   ```bash
   uv run agentseek ctx retrieve --scope my-scope --query "..."
   ```

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| `agentseek ctx` 提示需要 `agentseek-contextseek` | 当前项目未安装该包。 | 运行 `uv add agentseek-contextseek`。 |
| ContextSeek 报 backend 配置缺失 | 存储或 backend 设置缺失。 | 添加所需的 `AGENTSEEK_CTX_*` 值。 |

## 回退

移除依赖，并删除你配置的存储目录。

```bash
uv remove agentseek-contextseek
rm -rf .contextseek/store
```

## 相关

- contrib: [agentseek-contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md)
- 参考: [CLI 参考](../reference/cli.zh.md), [包参考](../reference/packages.zh.md)
