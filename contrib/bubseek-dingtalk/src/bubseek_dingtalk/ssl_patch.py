"""
Monkey-patch websockets and requests to disable SSL verification for DingTalk APIs.

dingtalk_stream uses websockets (WSS) and requests (HTTPS) without exposing ssl/verify options.
Corporate proxies often cause CERTIFICATE_VERIFY_FAILED. Patches apply on import.
"""

from __future__ import annotations

import ssl

import requests
import websockets

# --- websockets (WSS, used by dingtalk_stream for stream connection) ---
_ws_orig = websockets.connect


def _ws_patched(uri, *args, **kwargs):
    if "ssl" not in kwargs and str(uri).startswith("wss://"):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs["ssl"] = ctx
    return _ws_orig(uri, *args, **kwargs)


websockets.connect = _ws_patched

# --- requests (HTTPS, used by dingtalk_stream open_connection and bub_skills send) ---
_req_orig = requests.Session.request


def _req_patched(self, method, url, **kwargs):
    if "verify" not in kwargs and "api.dingtalk.com" in str(url):
        kwargs["verify"] = False
    return _req_orig(self, method, url, **kwargs)


requests.Session.request = _req_patched
