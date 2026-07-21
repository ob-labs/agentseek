"""Safety primitives for authored lifecycle values."""

from __future__ import annotations

import ntpath
import re
from pathlib import Path
from typing import Literal
from urllib.parse import SplitResult, parse_qsl, urlsplit

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
_BARE_EXECUTABLE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
_PLACEHOLDER_PATTERN = re.compile(r"\$\{|\{\{")

ServiceKind = Literal["web", "api", "protocol", "database", "other"]
ReferenceRel = Literal["docs", "api_docs", "studio"]

_SERVICE_SCHEMES: dict[ServiceKind, frozenset[str]] = {
    "web": frozenset({"http", "https"}),
    "api": frozenset({"http", "https", "ws", "wss"}),
    "protocol": frozenset({"http", "https", "ws", "wss"}),
    "database": frozenset({"mysql"}),
    "other": frozenset({"http", "https", "ws", "wss", "mysql"}),
}
_V1_ENDPOINT_SCHEMES = frozenset({"http", "https", "ws", "wss", "mysql"})
_HTTP_SCHEMES = frozenset({"http", "https"})


class UnsafeProjectPathError(ValueError):
    """A project-relative path failed lexical or resolved confinement."""

    def __init__(self) -> None:
        super().__init__("project path is unsafe")


def validate_identifier(value: str) -> str:
    """Return a lifecycle identifier after enforcing its safe grammar."""
    if _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise ValueError
    return value


def validate_bare_executable(value: str) -> str:
    """Return a bare executable name after enforcing its safe grammar."""
    if value in {".", ".."} or _BARE_EXECUTABLE_PATTERN.fullmatch(value) is None:
        raise ValueError
    return value


def validate_service_url(value: str, kind: ServiceKind) -> str:
    """Validate and return a literal v2 service endpoint."""
    _validate_absolute_url(value, allowed_schemes=_SERVICE_SCHEMES[kind])
    return value


def validate_check_target(value: str) -> str:
    """Validate and return a literal HTTP check target."""
    _validate_absolute_url(value, allowed_schemes=_HTTP_SCHEMES)
    return value


def validate_reference_url(rel: ReferenceRel, value: str) -> str:
    """Validate and return a v2 typed reference URL."""
    if rel == "docs":
        _validate_absolute_url(value, allowed_schemes=frozenset({"https"}))
    elif rel == "api_docs":
        parsed = _validate_absolute_url(value, allowed_schemes=_HTTP_SCHEMES)
        if parsed.scheme == "http" and not _is_api_docs_loopback(parsed.hostname):
            raise ValueError
    elif rel == "studio":
        parsed = _validate_absolute_url(
            value,
            allowed_schemes=frozenset({"https"}),
            allow_query=True,
        )
        _validate_studio_query(parsed.query)
    else:
        raise ValueError
    return value


def safe_v1_endpoint(value: str, *, http_only: bool = False) -> str | None:
    """Return a complete safe v1 endpoint literal, or omit it in full."""
    try:
        _validate_absolute_url(
            value,
            allowed_schemes=_HTTP_SCHEMES if http_only else _V1_ENDPOINT_SCHEMES,
        )
    except (TypeError, ValueError):
        return None
    return value


def _validate_absolute_url(
    value: str,
    *,
    allowed_schemes: frozenset[str],
    allow_query: bool = False,
) -> SplitResult:
    if not isinstance(value, str) or _contains_unsafe_url_literal(value):
        raise ValueError
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        raise ValueError from None

    if parsed.scheme not in allowed_schemes or not hostname:
        raise ValueError
    if parsed.username is not None or parsed.password is not None:
        raise ValueError
    if _has_empty_port(parsed) or (port is not None and not 0 <= port <= 65535):
        raise ValueError
    if (parsed.query and not allow_query) or parsed.fragment:
        raise ValueError
    return parsed


def _contains_unsafe_url_literal(value: str) -> bool:
    return _PLACEHOLDER_PATTERN.search(value) is not None or any(ord(char) <= 0x1F or ord(char) == 0x7F for char in value)


def _has_empty_port(parsed: SplitResult) -> bool:
    return parsed.netloc.rsplit("@", 1)[-1].endswith(":")


def _is_api_docs_loopback(hostname: str | None) -> bool:
    if hostname == "localhost":
        return True
    try:
        import ipaddress

        return ipaddress.ip_address(hostname).is_loopback
    except ValueError:
        return False


def _validate_studio_query(query: str) -> None:
    if not query:
        return
    _reject_invalid_percent_escapes(query)
    try:
        params = parse_qsl(query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        raise ValueError from None
    raw_keys = [part.partition("=")[0] for part in query.split("&")]
    if len(params) != 1 or len(raw_keys) != 1 or raw_keys[0] != "baseUrl" or params[0][0] != "baseUrl":
        raise ValueError
    _validate_absolute_url(params[0][1], allowed_schemes=_HTTP_SCHEMES)


def _reject_invalid_percent_escapes(value: str) -> None:
    for index, char in enumerate(value):
        if char == "%" and (index + 2 >= len(value) or not all(part in "0123456789abcdefABCDEF" for part in value[index + 1 : index + 3])):
            raise ValueError


def resolve_confined_project_path(project_root: Path, value: str, *, allow_dot: bool = False) -> Path:
    """Resolve a project-relative path only when it remains confined to the root."""
    if _path_is_lexically_unsafe(value, allow_dot=allow_dot):
        raise UnsafeProjectPathError()

    try:
        root = project_root.resolve(strict=False)
        candidate = (root / value).resolve(strict=False)
        candidate.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        raise UnsafeProjectPathError() from None
    return candidate


def _path_is_lexically_unsafe(value: str, *, allow_dot: bool) -> bool:
    if not value.strip() or "\x00" in value:
        return True
    if Path(value).is_absolute() or ntpath.isabs(value) or ntpath.splitdrive(value)[0]:
        return True
    segments = re.split(r"[/\\]", value)
    if all(segment in {"", "."} for segment in segments):
        return not allow_dot
    return ".." in segments


__all__ = [
    "UnsafeProjectPathError",
    "resolve_confined_project_path",
    "validate_bare_executable",
    "validate_identifier",
]
