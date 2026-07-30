from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest


def _is_unavailable_symlink_capability(exc: OSError) -> bool:
    """Return whether Windows denied symlink creation for missing privilege."""

    return getattr(exc, "winerror", None) == 1314


@pytest.fixture
def create_symlink(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Callable[..., None]:
    """Create a test symlink or skip when the runner does not permit it."""

    # pytest's ``tmp_path`` fixture creates its ``pytest-current`` link with
    # ``Path.symlink_to``. Resolve it before temporarily replacing that method
    # so an unavailable symlink capability skips only the test's own link.
    del tmp_path

    def _create(link: Path, target: Path, *, target_is_directory: bool = False) -> None:
        try:
            original_symlink_to(link, target, target_is_directory=target_is_directory)
        except OSError as exc:
            if _is_unavailable_symlink_capability(exc):
                pytest.skip(f"symlink creation is unavailable in this environment: {exc}")
            raise

    original_symlink_to = Path.symlink_to
    monkeypatch.setattr(
        Path,
        "symlink_to",
        lambda link, target, target_is_directory=False: _create(
            link,
            target,
            target_is_directory=target_is_directory,
        ),
    )
    return _create
