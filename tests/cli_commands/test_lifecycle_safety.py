from __future__ import annotations

from pathlib import Path

import pytest

import agentseek.cli.lifecycle.safety as safety
from agentseek.cli.lifecycle.safety import (
    UnsafeProjectPathError,
    resolve_confined_project_path,
    safe_v1_endpoint,
    validate_bare_executable,
    validate_check_target,
    validate_identifier,
    validate_reference_url,
    validate_service_url,
)


@pytest.mark.parametrize("value", ["frontend_2", "service-1", "a1"])
def test_validate_identifier_accepts_lifecycle_identifiers(value: str) -> None:
    assert validate_identifier(value) == value


@pytest.mark.parametrize(
    "value",
    ["", "has space", "dotted.id", "-option", "path/value", r"path\value", "line\nbreak", "control\x00"],
)
def test_validate_identifier_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(ValueError):
        validate_identifier(value)


@pytest.mark.parametrize("value", ["docker-compose", "python3.12", "tool+variant"])
def test_validate_bare_executable_accepts_safe_bare_names(value: str) -> None:
    assert validate_bare_executable(value) == value


@pytest.mark.parametrize(
    "value",
    ["", "has space", "-option", "path/value", r"path\value", ".", "..", "line\nbreak", "control\x1f"],
)
def test_validate_bare_executable_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(ValueError):
        validate_bare_executable(value)


def test_resolve_confined_project_path_accepts_missing_descendant(tmp_path: Path) -> None:
    assert resolve_confined_project_path(tmp_path, "missing/nested") == (tmp_path / "missing" / "nested").resolve()


def test_resolve_confined_project_path_accepts_dot_only_when_allowed(tmp_path: Path) -> None:
    assert resolve_confined_project_path(tmp_path, ".", allow_dot=True) == tmp_path.resolve()

    with pytest.raises(UnsafeProjectPathError):
        resolve_confined_project_path(tmp_path, ".")


@pytest.mark.parametrize("value", ["./", "././", ".\\", ".\\.\\"])
def test_resolve_confined_project_path_rejects_root_equivalent_non_cwd_paths(tmp_path: Path, value: str) -> None:
    with pytest.raises(UnsafeProjectPathError) as exc_info:
        resolve_confined_project_path(tmp_path, value)

    assert str(exc_info.value) == "project path is unsafe"


@pytest.mark.parametrize("value", ["", "   ", "\t"])
def test_resolve_confined_project_path_rejects_blank_non_cwd_values(tmp_path: Path, value: str) -> None:
    with pytest.raises(UnsafeProjectPathError) as exc_info:
        resolve_confined_project_path(tmp_path, value)

    assert str(exc_info.value) == "project path is unsafe"


@pytest.mark.parametrize(
    "value",
    [
        "/absolute/path",
        r"C:\absolute\path",
        "C:/absolute/path",
        r"C:relative\path",
        r"\\server\share",
        "//server/share",
    ],
)
def test_resolve_confined_project_path_rejects_posix_and_windows_absolute_paths(tmp_path: Path, value: str) -> None:
    with pytest.raises(UnsafeProjectPathError) as exc_info:
        resolve_confined_project_path(tmp_path, value)

    assert str(exc_info.value) == "project path is unsafe"


@pytest.mark.parametrize("value", ["..", "../escape", r"..\escape", "safe/../escape", r"safe\..\escape"])
def test_resolve_confined_project_path_rejects_every_parent_segment_in_both_styles(tmp_path: Path, value: str) -> None:
    with pytest.raises(UnsafeProjectPathError) as exc_info:
        resolve_confined_project_path(tmp_path, value)

    assert str(exc_info.value) == "project path is unsafe"


def test_resolve_confined_project_path_rejects_nul_without_echoing_value(tmp_path: Path) -> None:
    value = "safe\x00name"

    with pytest.raises(UnsafeProjectPathError) as exc_info:
        resolve_confined_project_path(tmp_path, value)

    assert str(exc_info.value) == "project path is unsafe"


def test_resolve_confined_project_path_rejects_leaf_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-leaf"
    outside.mkdir()
    (tmp_path / "leaf-escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(UnsafeProjectPathError):
        resolve_confined_project_path(tmp_path, "leaf-escape")


def test_resolve_confined_project_path_rejects_intermediate_symlink_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-intermediate"
    outside.mkdir()
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "escape").symlink_to(outside, target_is_directory=True)

    with pytest.raises(UnsafeProjectPathError):
        resolve_confined_project_path(tmp_path, "nested/escape/missing")


@pytest.mark.parametrize(
    ("kind", "url"),
    [
        ("web", "http://service.test"),
        ("web", "https://service.test"),
        ("api", "http://service.test"),
        ("api", "https://service.test"),
        ("api", "ws://service.test"),
        ("api", "wss://service.test"),
        ("protocol", "http://service.test"),
        ("protocol", "https://service.test"),
        ("protocol", "ws://service.test"),
        ("protocol", "wss://service.test"),
        ("database", "mysql://service.test"),
        ("other", "http://service.test"),
        ("other", "https://service.test"),
        ("other", "ws://service.test"),
        ("other", "wss://service.test"),
        ("other", "mysql://service.test"),
    ],
)
def test_validate_service_url_accepts_every_allowed_kind_scheme_pair(kind: str, url: str) -> None:
    assert validate_service_url(url, kind) == url


@pytest.mark.parametrize(
    ("kind", "url"),
    [
        ("web", "ws://service.test"),
        ("web", "wss://service.test"),
        ("web", "mysql://service.test"),
        ("api", "mysql://service.test"),
        ("protocol", "mysql://service.test"),
        ("database", "http://service.test"),
        ("database", "https://service.test"),
        ("database", "ws://service.test"),
        ("database", "wss://service.test"),
        ("other", "ftp://service.test"),
    ],
)
def test_validate_service_url_rejects_every_disallowed_kind_scheme_pair(kind: str, url: str) -> None:
    with pytest.raises(ValueError):
        validate_service_url(url, kind)


@pytest.mark.parametrize(
    "url",
    [
        "/relative/path",
        "service.test/path",
        "https:/missing-slash.test",
        "https://",
        "https:///missing-host",
        "https://:443/path",
        "https://[::1",
        "https://user:password@service.test",
        "https://user@service.test",
        "https://service.test:invalid",
        "https://service.test:65536",
        "https://service.test?query=value",
        "https://service.test#fragment",
        "https://service.test/${HOST}",
        "https://service.test/{{ host }}",
        "https://service.test/line\nbreak",
        "https://service.test/control\x1f",
    ],
)
def test_validate_service_url_rejects_unsafe_literal_forms(url: str) -> None:
    with pytest.raises(ValueError):
        validate_service_url(url, "web")


@pytest.mark.parametrize("url", ["http://check.test", "https://check.test:443/health"])
def test_validate_check_target_accepts_absolute_http_urls(url: str) -> None:
    assert validate_check_target(url) == url


@pytest.mark.parametrize(
    "url",
    [
        "ws://check.test",
        "wss://check.test",
        "mysql://check.test",
        "https://user@check.test",
        "https://check.test?live=true",
        "https://check.test#status",
        "https://check.test/${HOST}",
    ],
)
def test_validate_check_target_rejects_unsafe_or_non_http_urls(url: str) -> None:
    with pytest.raises(ValueError):
        validate_check_target(url)


@pytest.mark.parametrize("url", ["https://docs.example.test", "https://docs.example.test/guide"])
def test_validate_reference_url_accepts_docs_https_without_query(url: str) -> None:
    assert validate_reference_url("docs", url) == url


@pytest.mark.parametrize(
    "url",
    ["http://docs.example.test", "https://user@docs.example.test", "https://docs.example.test?a=b", "https://docs.example.test#top"],
)
def test_validate_reference_url_rejects_unsafe_docs_urls(url: str) -> None:
    with pytest.raises(ValueError):
        validate_reference_url("docs", url)


@pytest.mark.parametrize(
    "url",
    [
        "https://api.example.test/openapi.json",
        "http://127.0.0.0/openapi.json",
        "http://127.255.255.255/openapi.json",
        "http://[::1]/openapi.json",
        "http://localhost/openapi.json",
    ],
)
def test_validate_reference_url_accepts_api_docs_https_or_exact_loopback_http(url: str) -> None:
    assert validate_reference_url("api_docs", url) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://126.255.255.255/openapi.json",
        "http://128.0.0.0/openapi.json",
        "http://[::2]/openapi.json",
        "http://localhost.example.test/openapi.json",
        "ws://127.0.0.1/openapi.json",
        "https://api.example.test?format=json",
        "https://api.example.test#operations",
    ],
)
def test_validate_reference_url_rejects_non_loopback_or_unsafe_api_docs_urls(url: str) -> None:
    with pytest.raises(ValueError):
        validate_reference_url("api_docs", url)


@pytest.mark.parametrize(
    "url",
    [
        "https://studio.example.test",
        "https://studio.example.test/?baseUrl=https%3A%2F%2Fapi.example.test%2Fv1",
        "https://studio.example.test/?baseUrl=http%3A%2F%2Fapi.example.test%3A8080%2Fv1",
    ],
)
def test_validate_reference_url_accepts_studio_without_query_or_one_safe_base_url(url: str) -> None:
    assert validate_reference_url("studio", url) == url


@pytest.mark.parametrize(
    "url",
    [
        "http://studio.example.test",
        "https://user@studio.example.test",
        "https://studio.example.test#trace",
        "https://studio.example.test/?baseUrl",
        "https://studio.example.test/?baseUrl=",
        "https://studio.example.test/?baseUrl=https%3A%2F%2Fapi.example.test&baseUrl=https%3A%2F%2Fother.example.test",
        "https://studio.example.test/?baseUrl=https%3A%2F%2Fapi.example.test&view=graph",
        "https://studio.example.test/?api%5Fkey=secret",
        "https://studio.example.test/?%62aseUrl=https%3A%2F%2Fapi.example.test",
        "https://studio.example.test/?baseUrl=https%3A%2F%2Fapi.example.test%3Ftoken%3Dsecret",
        "https://studio.example.test/?baseUrl=https%3A%2F%2Fuser%40api.example.test",
        "https://studio.example.test/?baseUrl=https%3A%2F%2Fapi.example.test%23fragment",
        "https://studio.example.test/?baseUrl=relative%2Fapi",
        "https://studio.example.test/?baseUrl=https%3A%2F%2Fapi.example.test%3Ainvalid",
        "https://studio.example.test/?baseUrl=https%3A%2F%2Fapi.example.test%3A65536",
        "https://studio.example.test/?baseUrl=https%3A%2F%2Fapi.example.test%2F%24%7BHOST%7D",
        "https://studio.example.test/?baseUrl=%ZZ",
    ],
)
def test_validate_reference_url_rejects_studio_disallowed_or_unsafe_query(url: str) -> None:
    with pytest.raises(ValueError):
        validate_reference_url("studio", url)


@pytest.mark.parametrize(
    "value",
    [
        "HTTPS://Example.test:443/path",
        "ws://socket.example.test",
        "wss://socket.example.test",
        "mysql://database.example.test:3306/schema",
    ],
)
def test_safe_v1_endpoint_returns_the_original_safe_literal(value: str) -> None:
    assert safe_v1_endpoint(value) == value


@pytest.mark.parametrize("value", ["http://service.test", "https://service.test"])
def test_safe_v1_endpoint_http_only_accepts_http_schemes(value: str) -> None:
    assert safe_v1_endpoint(value, http_only=True) == value


@pytest.mark.parametrize(
    "value",
    [
        "ws://socket.example.test",
        "wss://socket.example.test",
        "mysql://database.example.test",
        "https://user@service.test",
        "https://service.test?token=secret",
        "https://service.test#fragment",
        "https://service.test/${HOST}",
        "https://service.test:invalid",
    ],
)
def test_safe_v1_endpoint_returns_none_for_http_only_or_unsafe_values(value: str) -> None:
    assert safe_v1_endpoint(value, http_only=True) is None


@pytest.mark.parametrize(
    "value",
    [
        "/relative",
        "https://",
        "https://user@service.test",
        "https://service.test?token=secret",
        "https://service.test#fragment",
        "https://service.test/${HOST}",
        "https://service.test:65536",
    ],
)
def test_safe_v1_endpoint_returns_none_without_partial_redaction(value: str) -> None:
    assert safe_v1_endpoint(value) is None


@pytest.mark.parametrize("url", ["https://service.test?", "https://service.test#"])
def test_validate_service_url_rejects_explicit_empty_query_or_fragment_delimiters(url: str) -> None:
    with pytest.raises(ValueError):
        validate_service_url(url, "web")


@pytest.mark.parametrize("url", ["https://check.test?", "https://check.test#"])
def test_validate_check_target_rejects_explicit_empty_query_or_fragment_delimiters(url: str) -> None:
    with pytest.raises(ValueError):
        validate_check_target(url)


@pytest.mark.parametrize(
    ("rel", "url"),
    [
        ("docs", "https://docs.test?"),
        ("docs", "https://docs.test#"),
        ("api_docs", "http://127.0.0.1/openapi?"),
        ("api_docs", "http://127.0.0.1/openapi#"),
        ("studio", "https://studio.test?"),
        ("studio", "https://studio.test#"),
        ("studio", "https://studio.test?baseUrl=https%3A%2F%2Fapi.test#"),
    ],
)
def test_validate_reference_url_rejects_explicit_empty_query_or_fragment_delimiters(rel: str, url: str) -> None:
    with pytest.raises(ValueError):
        validate_reference_url(rel, url)


@pytest.mark.parametrize("value", ["https://service.test?", "https://service.test#"])
def test_safe_v1_endpoint_omits_explicit_empty_query_or_fragment_delimiters(value: str) -> None:
    assert safe_v1_endpoint(value) is None


@pytest.mark.parametrize(
    "url",
    [
        "https://studio.test?baseUrl=https%3A%2F%2Fapi.test%3F",
        "https://studio.test?baseUrl=https%3A%2F%2Fapi.test%23",
    ],
)
def test_validate_reference_url_rejects_studio_nested_endpoint_with_empty_delimiter(url: str) -> None:
    with pytest.raises(ValueError):
        validate_reference_url("studio", url)


@pytest.mark.parametrize(
    "url",
    [
        "http://[::1%25lo0]/openapi",
        "http://[::1%lo0]/openapi",
        "http://[0:0:0:0:0:0:0:1]/openapi",
        "http://[::01]/openapi",
        "http://[::ffff:127.0.0.1]/openapi",
    ],
)
def test_validate_reference_url_rejects_noncanonical_ipv6_api_docs_loopback_hosts(url: str) -> None:
    with pytest.raises(ValueError):
        validate_reference_url("api_docs", url)


def test_lifecycle_endpoint_interfaces_are_publicly_exported() -> None:
    assert {
        "ServiceKind",
        "ReferenceRel",
        "validate_service_url",
        "validate_check_target",
        "validate_reference_url",
        "safe_v1_endpoint",
    }.issubset(safety.__all__)
