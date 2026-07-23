"""Measure shallow-clone and optimized template-fetch timings.

The command intentionally reports failures as JSON records so a blocked
network still produces reproducible diagnostic output.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

DEFAULT_REPOSITORY = "https://github.com/ob-labs/agentseek"


class _OptimizedFetchFailed(RuntimeError):
    def __str__(self) -> str:
        return "optimized fetch returned no cache"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=DEFAULT_REPOSITORY, help="Repository URL without the .git suffix.")
    parser.add_argument("--ref", default="main", help="Git branch or archive ref to measure.")
    parser.add_argument("--template", default="langchain/default", help="Template key in <type>/<name> form.")
    parser.add_argument("--runs", type=int, default=1, help="Number of cold runs for each strategy.")
    parser.add_argument("--timeout-seconds", type=float, default=60.0, help="Per-operation Git timeout.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    args = parser.parse_args(argv)
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")
    if "/" not in args.template:
        parser.error("--template must use <type>/<name> form")
    return args


def directory_size(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(path.stat().st_size for path in root.rglob("*") if path.is_file())


def _write_cookiecutter_config(root: Path, cache_dir: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    config_path = root / "cookiecutter.json"
    config_path.write_text(json.dumps({"cookiecutters_dir": str(cache_dir)}), encoding="utf-8")
    return config_path


def _record(mode: str, run: int, started: float, *, root: Path, error: Exception | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "mode": mode,
        "run": run,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "bytes": directory_size(root),
    }
    if error is None:
        result["status"] = "ok"
    else:
        result["status"] = "error"
        result["error"] = f"{type(error).__name__}: {error}"
    return result


def _run_shallow_clone(
    *,
    repo: str,
    ref: str,
    destination: Path,
    run: int = 1,
    timeout_seconds: float = 60.0,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        git_executable = shutil.which("git")
        if git_executable is None:
            raise FileNotFoundError
        subprocess.run(  # noqa: S603 - arguments are passed without a shell
            [git_executable, "clone", "--depth", "1", "--branch", ref, f"{repo}.git", str(destination)],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return _record("shallow_clone", run, started, root=destination)
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return _record("shallow_clone", run, started, root=destination, error=exc)


def _run_optimized_fetch(
    *,
    repo: str,
    ref: str,
    template_key: str,
    cache_dir: Path,
    config_root: Path,
    mode: str,
    run: int,
) -> dict[str, Any]:
    from agentseek.cli.commands.create import _download_template_tarball

    project_type, template_name = template_key.split("/", 1)
    config_path = _write_cookiecutter_config(config_root, cache_dir)
    previous_config = os.environ.get("COOKIECUTTER_CONFIG")
    os.environ["COOKIECUTTER_CONFIG"] = str(config_path)
    started = time.perf_counter()
    try:
        fetched_root = _download_template_tarball(
            project_type,
            template_name,
            repo_url=repo,
            checkout=ref,
        )
        if fetched_root is None:
            return _record(mode, run, started, root=cache_dir, error=_OptimizedFetchFailed())
        return _record(mode, run, started, root=cache_dir)
    except Exception as exc:  # benchmark must report network/runtime failures
        return _record(mode, run, started, root=cache_dir, error=exc)
    finally:
        if previous_config is None:
            os.environ.pop("COOKIECUTTER_CONFIG", None)
        else:
            os.environ["COOKIECUTTER_CONFIG"] = previous_config


def run_benchmark(args: argparse.Namespace) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="agentseek-template-benchmark-") as temporary:
        root = Path(temporary)
        for run in range(1, args.runs + 1):
            records.append(
                _run_shallow_clone(
                    repo=args.repo,
                    ref=args.ref,
                    destination=root / f"clone-{run}",
                    run=run,
                    timeout_seconds=args.timeout_seconds,
                )
            )
            records.append(
                _run_optimized_fetch(
                    repo=args.repo,
                    ref=args.ref,
                    template_key=args.template,
                    cache_dir=root / f"cold-cache-{run}",
                    config_root=root / f"cold-config-{run}",
                    mode="optimized_cold",
                    run=run,
                )
            )

        warm_cache = root / "warm-cache"
        warm_config = root / "warm-config"
        for run in range(1, args.runs + 1):
            _run_optimized_fetch(
                repo=args.repo,
                ref=args.ref,
                template_key=args.template,
                cache_dir=warm_cache,
                config_root=warm_config,
                mode="optimized_warm_setup",
                run=run,
            )
            records.append(
                _run_optimized_fetch(
                    repo=args.repo,
                    ref=args.ref,
                    template_key=args.template,
                    cache_dir=warm_cache,
                    config_root=warm_config,
                    mode="optimized_warm",
                    run=run,
                )
            )

    return {
        "schema_version": 1,
        "repository": args.repo,
        "ref": args.ref,
        "template": args.template,
        "runs": args.runs,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "records": records,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_benchmark(args)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if all(record["status"] == "ok" for record in result["records"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
