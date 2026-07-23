"""Tests for the template-fetch benchmark helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from scripts.benchmark_template_fetch import (
    _run_optimized_fetch,
    _run_shallow_clone,
    _write_cookiecutter_config,
    directory_size,
    main,
    parse_args,
)


def test_parse_args_captures_template_and_run_count() -> None:
    args = parse_args(["--template", "langchain/default", "--runs", "2"])

    assert args.template == "langchain/default"
    assert args.runs == 2
    assert args.ref == "main"


def test_directory_size_counts_nested_files(tmp_path: Path) -> None:
    (tmp_path / "nested").mkdir()
    (tmp_path / "one.bin").write_bytes(b"123")
    (tmp_path / "nested" / "two.bin").write_bytes(b"4567")

    assert directory_size(tmp_path) == 7


def test_shallow_clone_failure_is_reported_without_raising(tmp_path: Path) -> None:
    with patch(
        "scripts.benchmark_template_fetch.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, ["git", "clone"]),
    ):
        result = _run_shallow_clone(
            repo="https://github.com/ob-labs/agentseek",
            ref="main",
            destination=tmp_path / "clone",
        )

    assert result["status"] == "error"
    assert "CalledProcessError" in result["error"]


def test_shallow_clone_timeout_is_reported_without_raising(tmp_path: Path) -> None:
    with patch(
        "scripts.benchmark_template_fetch.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["git", "clone"], timeout=3),
    ):
        result = _run_shallow_clone(
            repo="https://github.com/ob-labs/agentseek",
            ref="main",
            destination=tmp_path / "clone",
            timeout_seconds=3,
        )

    assert result["status"] == "error"
    assert "TimeoutExpired" in result["error"]


def test_cookiecutter_config_is_isolated(tmp_path: Path) -> None:
    config = _write_cookiecutter_config(tmp_path / "config", tmp_path / "cache")

    assert config.is_file()
    assert '"cookiecutters_dir"' in config.read_text(encoding="utf-8")


def test_optimized_fetch_none_is_reported_as_error(tmp_path: Path) -> None:
    with patch("agentseek.cli.commands.create._download_template_tarball", return_value=None):
        result = _run_optimized_fetch(
            repo="https://github.com/ob-labs/agentseek",
            ref="main",
            template_key="langchain/default",
            cache_dir=tmp_path / "cache",
            config_root=tmp_path / "config",
            mode="optimized_cold",
            run=1,
        )

    assert result["status"] == "error"
    assert "returned no cache" in result["error"]


def test_main_returns_nonzero_when_any_measurement_fails() -> None:
    result = {
        "records": [
            {"status": "ok"},
            {"status": "error"},
        ]
    }
    with patch("scripts.benchmark_template_fetch.run_benchmark", return_value=result):
        assert main(["--template", "langchain/default"]) == 1
