"""Process-wide TLS verification overrides for local proxy environments.

This is intentionally gated by environment variables so it only affects
explicitly opted-in local runs.
"""

from __future__ import annotations

import os
import ssl


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _disable_tls_verification() -> None:
    original_create_default_context = ssl.create_default_context

    def _unverified_context(*args: object, **kwargs: object) -> ssl.SSLContext:
        context = original_create_default_context(*args, **kwargs)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    ssl._create_default_https_context = ssl._create_unverified_context
    ssl.create_default_context = _unverified_context

    try:
        import requests.sessions

        original_request = requests.sessions.Session.request

        def _request(self: requests.sessions.Session, method: str, url: str, **kwargs: object):  # type: ignore[no-untyped-def]
            kwargs.setdefault("verify", False)
            return original_request(self, method, url, **kwargs)

        requests.sessions.Session.request = _request
    except ImportError:
        pass

    try:
        import httpx

        original_client_init = httpx.Client.__init__
        original_async_client_init = httpx.AsyncClient.__init__

        def _client_init(self: httpx.Client, *args: object, **kwargs: object) -> None:
            kwargs.setdefault("verify", False)
            original_client_init(self, *args, **kwargs)

        def _async_client_init(self: httpx.AsyncClient, *args: object, **kwargs: object) -> None:
            kwargs.setdefault("verify", False)
            original_async_client_init(self, *args, **kwargs)

        httpx.Client.__init__ = _client_init
        httpx.AsyncClient.__init__ = _async_client_init
    except ImportError:
        pass


if _truthy(os.getenv("BUBSEEK_DISABLE_TLS_VERIFY")):
    _disable_tls_verification()
