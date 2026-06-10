---
title: 如何使用 ContextSeek
type: how-to
audience: [A2]
runs: yes
verified_on: 2026-05-28
sources:
  - src/agentseek/cli/runtime.py
  - contrib/agentseek-contextseek/README.md
---

# 如何使用 ContextSeek

当你希望在每次模型 turn 之前检索上下文、之后写回响应时使用本
指南，这就是语义上下文层。ContextSeek 由 `agentseek-contextseek`
contrib 包提供；`agentseek ctx` 会转发到其底层 `contextseek` CLI。

## 前置条件

- 已安装 `agentseek-contextseek` 插件：

  ```bash title="not executed in this run"
  agentseek plugin install agentseek-contextseek
  ```

  该命令会安装 ContextSeek runtime plugin，并让同一环境里的 `agentseek ctx`
  转发命令可用。

- 已配置 ContextSeek 自身的 backend。见
  [contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md)。

## 步骤

1. 确认子命令已连接：

   ```bash
   uv run agentseek ctx --help
   ```

   ```text title="output"
   usage: contextseek [-h]
                      {add,retrieve,expand,compact,forget,delete,overview,tools,metrics,dream,feedback,upstream,evidence-chain,chain-confidence,skill-tools,skill-context,skill-import,items}
                      ...
   ```

   输出是上游 `contextseek` argparse 的 help；agentseek 不会
   重新包装。

2. 添加一条上下文项：

   ```bash title="not executed in this run"
   uv run agentseek ctx add --scope my-scope --text "..."
   ```

3. 检索排序命中：

   ```bash title="not executed in this run"
   uv run agentseek ctx retrieve --scope my-scope --query "..."
   ```

## 子命令索引

转发的 `contextseek` CLI 暴露 (来自
`agentseek ctx --help`)：`add`、`retrieve`、`expand`、`compact`、`forget`、
`delete`、`overview`、`tools`、`metrics`、`dream`、`feedback`、`upstream`、
`evidence-chain`、`chain-confidence`、`skill-tools`、`skill-context`、
`skill-import`、`items`。每个子命令的语义见该包的 README。

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| `agentseek ctx` 报 command not found | 未安装 `agentseek-contextseek` | `agentseek plugin install agentseek-contextseek`。 |
| `contextseek` 报 backend 缺失 | 配置未就绪 | 见 [contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md)。 |

## 回退

ContextSeek 的存储由 backend 维护（`agentseek-contextseek` README
说明了如何移除）。要卸载该插件：

```bash title="not executed in this run"
uv run agentseek plugin uninstall agentseek-contextseek
```

## 相关

- contrib: [agentseek-contextseek README](https://github.com/ob-labs/agentseek/blob/main/contrib/agentseek-contextseek/README.md)
- 参考: [CLI 参考](../reference/cli.zh.md), [包参考](../reference/packages.zh.md)
