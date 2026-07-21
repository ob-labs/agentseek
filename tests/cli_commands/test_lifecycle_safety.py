from __future__ import annotations

from pathlib import Path

import pytest

from agentseek.cli.lifecycle.safety import (
    UnsafeProjectPathError,
    resolve_confined_project_path,
    validate_bare_executable,
    validate_identifier,
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
