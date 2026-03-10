# bubseek-dingtalk

DingTalk channel for Bub using Stream Mode.

## What It Provides

- Bub plugin entry point: `dingtalk`
- WebSocket Stream Mode for receiving messages
- DingTalk skill (`bub_skills/dingtalk`) for sending messages via Robot API
- `dingtalk_send.py` script for agent to invoke
- Supports private (1:1) and group chats

## Installation

As optional extra:

```bash
uv sync --extra dingtalk
# or
pip install bubseek[dingtalk]
```

From bubseek repo (development):

```bash
uv add ./contrib/bubseek-dingtalk
```

## Configuration

Set these environment variables (or in `.env`):

| Variable | Description |
| --- | --- |
| `BUB_DINGTALK_CLIENT_ID` | AppKey from DingTalk Open Platform |
| `BUB_DINGTALK_CLIENT_SECRET` | AppSecret |
| `BUB_DINGTALK_ALLOW_USERS` | Comma-separated staff_ids to allow, or `*` for all |

## DingTalk App Setup

1. Create an app in [DingTalk Open Platform](https://open.dingtalk.com/)
2. Enable "Robot" capability and "Stream Mode"
3. Configure callback URL if required
4. Use AppKey as `BUB_DINGTALK_CLIENT_ID` and AppSecret as `BUB_DINGTALK_CLIENT_SECRET`

## Skill

Outbound messages go through the DingTalk skill. The channel's `send()` delegates to `bub_skills.dingtalk.send.send_message()`. Agents can also invoke the script directly:

```bash
uv run python -m bub_skills.dingtalk.scripts.dingtalk_send --chat-id <CHAT_ID> --content "<TEXT>"
```

See `SKILL.md` for agent-facing execution instructions.

## Verify Inbound Flow

To simulate the inbound path (DingTalk -> agent loop):

```bash
# From bubseek workspace root
uv run python contrib/bubseek-dingtalk/tests/test_inbound_flow.py
```

Or run the pytest:

```bash
uv run pytest contrib/bubseek-dingtalk/tests/test_inbound_flow.py -v
```
