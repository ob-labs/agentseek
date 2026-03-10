"""DingTalk send logic - shared by channel and skill script."""

from __future__ import annotations

import json
from typing import Any

import requests

OPENAPI_BASE = "https://api.dingtalk.com"
TOKEN_URL = f"{OPENAPI_BASE}/v1.0/oauth2/accessToken"


def get_access_token(client_id: str, client_secret: str, *, verify: bool = True) -> str:
    """Get DingTalk access token."""
    resp = requests.post(
        TOKEN_URL,
        json={"appKey": client_id, "appSecret": client_secret},
        timeout=30,
        verify=verify,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("accessToken")
    if not token:
        raise RuntimeError(f"Failed to get token: {data.get('message', 'unknown')}")
    return str(token)


def send_message(
    client_id: str,
    client_secret: str,
    chat_id: str,
    content: str,
    *,
    title: str = "Bub Reply",
    msg_key: str = "sampleMarkdown",
    verify: bool = True,
) -> dict[str, Any]:
    """
    Send a markdown message to DingTalk.
    chat_id: "group:<openConversationId>" for group, or user_id for 1:1.
    Used by both channel.send() and the skill script.
    """
    token = get_access_token(client_id, client_secret, verify=verify)
    headers = {
        "Content-Type": "application/json",
        "x-acs-dingtalk-access-token": token,
    }
    msg_param = {"text": content, "title": title}

    if chat_id.startswith("group:"):
        url = f"{OPENAPI_BASE}/v1.0/robot/groupMessages/send"
        payload = {
            "robotCode": client_id,
            "openConversationId": chat_id[6:],
            "msgKey": msg_key,
            "msgParam": json.dumps(msg_param, ensure_ascii=False),
        }
    else:
        url = f"{OPENAPI_BASE}/v1.0/robot/oToMessages/batchSend"
        payload = {
            "robotCode": client_id,
            "userIds": [chat_id],
            "msgKey": msg_key,
            "msgParam": json.dumps(msg_param, ensure_ascii=False),
        }

    resp = requests.post(url, json=payload, headers=headers, timeout=30, verify=verify)
    resp.raise_for_status()
    result = resp.json() if resp.text else {}
    errcode = result.get("errcode")
    if errcode not in (None, 0):
        raise RuntimeError(f"DingTalk send failed: errcode={errcode} msg={result.get('message', '')}")
    return result
