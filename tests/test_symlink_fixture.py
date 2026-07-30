"""Regression tests for the symlink-capability fixture."""

from __future__ import annotations

from pathlib import Path

import pytest


class _WindowsSymlinkPrivilegeError(OSError):
    winerror = 1314


def test_create_symlink_skips_only_missing_windows_privilege(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> None:
    def unavailable(*_args: object, **_kwargs: object) -> None:
        raise _WindowsSymlinkPrivilegeError

    monkeypatch.setattr(Path, "symlink_to", unavailable)
    create_symlink = request.getfixturevalue("create_symlink")

    with pytest.raises(pytest.skip.Exception):
        create_symlink(tmp_path / "link", tmp_path / "target")


def test_create_symlink_reraises_unrelated_os_errors(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    tmp_path: Path,
) -> None:
    def already_exists(*_args: object, **_kwargs: object) -> None:
        raise FileExistsError

    monkeypatch.setattr(Path, "symlink_to", already_exists)
    create_symlink = request.getfixturevalue("create_symlink")

    with pytest.raises(FileExistsError):
        create_symlink(tmp_path / "link", tmp_path / "target")
