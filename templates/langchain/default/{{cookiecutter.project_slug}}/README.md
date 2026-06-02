# {{ cookiecutter.project_name }}

A LangChain `create_agent` project with CopilotKit middleware, bound to
agentseek through `agentseek-langchain`.

## Quickstart

### Local AG-UI

```bash
uv sync
npm install --prefix frontend

cp .env.example .env
cp frontend/.env.example frontend/.env
# Optionally merge in the model credentials from your existing repository root `.env`.

uv run agentseek run --no-browser
```

The frontend defaults to `http://127.0.0.1:{{ cookiecutter.frontend_port }}`,
the CopilotKit runtime to `http://127.0.0.1:{{ cookiecutter.copilotkit_port }}/api/copilotkit`,
and the gateway to `http://127.0.0.1:{{ cookiecutter.gateway_port }}/agent`.

### Feishu Channel

This template also ships a first-class Feishu gateway path for group-chat use
cases.

1. Open the Feishu Open Platform and create or open a **self-built app**
   (`企业自建应用`).
2. Enable **Bot** capability (`机器人`).
3. Get the required values from these exact pages:
   - `AGENTSEEK_FEISHU_APP_ID`
     - Open **Credentials & Basic Info** (`凭证与基础信息`).
     - Copy **App ID**. It usually already starts with `cli_`; do not add an
       extra `cli_` prefix yourself.
   - `AGENTSEEK_FEISHU_APP_SECRET`
     - On the same **Credentials & Basic Info** page, copy **App Secret**.
   - `AGENTSEEK_FEISHU_VERIFICATION_TOKEN`
     - Open **Events & callbacks** (`事件与回调`).
     - Switch to the **Encryption Settings** (`加密策略`) tab.
     - Copy **Verification Token**.
   - `AGENTSEEK_FEISHU_ENCRYPT_KEY`
     - On the same **Encryption Settings** page, copy **Encrypt Key** if you
       enabled event encryption. Leave it unset otherwise.
4. Under **Events & callbacks** (`事件与回调`):
   - choose **long-connection mode** for local development;
   - subscribe to `im.message.receive_v1`.
5. Under **Permissions** (`权限管理`), grant message send permission. If you
   want the bot to understand ordinary group context instead of only explicit
   mentions, also grant the permission that allows reading all group messages.
6. Publish a version of the app, then add the bot to your test chat.
7. Fill the values into `.env`:

```bash
AGENTSEEK_FEISHU_APP_ID=
AGENTSEEK_FEISHU_APP_SECRET=
AGENTSEEK_FEISHU_VERIFICATION_TOKEN=
# AGENTSEEK_FEISHU_ENCRYPT_KEY=
```

Then start the Feishu-only gateway:

```bash
uv run serve-feishu
```

`serve-feishu` forces direct websocket connections by setting `NO_PROXY=*`
because macOS system SOCKS proxies can otherwise break the Feishu long
connection even when your shell environment looks clean.

If the bot does not react in Feishu, check these first:
- the app version was published after you changed permissions or events;
- `im.message.receive_v1` is actually subscribed;
- the bot was added to the chat;
- the app has permission to send messages;
- the app has the "read all group messages" style permission if you expect it
  to understand messages that did not mention it directly.

Author: {{ cookiecutter.author }}
