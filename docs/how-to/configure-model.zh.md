---
title: 如何配置模型提供方
type: how-to
audience: [A2, A4]
runs: yes
verified_on: 2026-06-12
sources:
  - src/agentseek/env.py
  - README.md
  - docs/index.md
---

# 如何配置模型提供方

当你要让 AgentSeek 调用自己的模型提供方时使用本页。

## 前置条件

- 一个可用的 AgentSeek 环境。
- 所选提供方的有效 API key。

## 步骤

1. 在运行 AgentSeek 的目录中创建或编辑 `.env`。

   ```bash title=".env"
   AGENTSEEK_MODEL=openrouter:moonshotai/kimi-k2:free
   AGENTSEEK_API_KEY=sk-or-v1-replace-me   # fake placeholder
   ```

2. 只有使用 OpenAI 兼容端点时，才需要添加 base URL。

   ```bash title=".env"
   AGENTSEEK_API_BASE=https://openrouter.ai/api/v1
   ```

3. 从同一目录启动 chat。

   ```bash
   agentseek chat
   ```

AgentSeek 也接受对应的 `BUB_*` 变量。两种前缀同时存在时，`BUB_*` 优先生效。

### CLI 快捷方式

按次运行时，可以直接传入进程环境变量：

```bash
AGENTSEEK_MODEL=openai:gpt-4o-mini \
AGENTSEEK_API_KEY=sk-replace-me \
agentseek chat
```

示例中的 key 是占位符。

## 故障排查

| 现象 | 可能原因 | 解决 |
| --- | --- | --- |
| `401 Unauthorized` | key 缺失或过期。 | 更新 `AGENTSEEK_API_KEY`。 |
| 请求打到错误端点 | provider 需要自定义 base URL。 | 设置 `AGENTSEEK_API_BASE`。 |
| `.env` 值被忽略 | shell 中存在同名 `BUB_*` 变量。 | 取消或更新该 shell 变量。 |

## 回退

从 `.env` 删除模型配置，或取消同名 shell 变量。

## 相关

- 参考: [环境变量参考](../reference/environment.zh.md)
- 概念解释: [agentseek 与 Bub 的关系](../explanation/bub-relationship.zh.md)
