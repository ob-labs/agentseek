# Agentseek Agent Instructions

## Chat channels (`$feishu`, `$telegram`)

When the message context includes a **channel tag** (e.g. `$feishu`, `$telegram`) and session/chat metadata, you are on an inbound chat channel.

- **Reply with plain text.** The framework delivers it to the user. Do not run shell commands or scripts just to answer the user.
- **Channel-specific send tools** (names vary by plugin: e.g. Feishu or Telegram helpers): use them only when you must send a message **from inside another tool** (e.g. progress during a long task), not for normal turn replies.
