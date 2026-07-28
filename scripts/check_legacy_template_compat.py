"""Exercise published AgentSeek 0.0.x template resolvers against the v1 mirror."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReleaseCase:
    distribution: str
    generation: str


CASES = {
    "0.0.1": ReleaseCase("agentseek-cli", "cookiecutter"),
    "0.0.2": ReleaseCase("agentseek-cli", "cookiecutter"),
    "0.0.3": ReleaseCase("agentseek", "cached"),
    "0.0.4": ReleaseCase("agentseek", "cached"),
    "0.0.5": ReleaseCase("agentseek", "repairing"),
}
REPRESENTATIVE_TEMPLATES = ("bub/default", "deepagents/default", "langchain/default")
CORE_REPOSITORY = "https://github.com/ob-labs/agentseek"


def _run(command: list[str], *, cwd: Path, env: dict[str, str]) -> str:
    result = subprocess.run(  # noqa: S603
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")
    if result.returncode:
        rendered = " ".join(command)
        message = f"command failed with exit code {result.returncode}: {rendered}"
        raise RuntimeError(message)
    return result.stdout


def _assert_v1_lifecycle(output_dir: Path, expected_template: str) -> None:
    lifecycle_files = list(output_dir.glob("*/.agentseek/lifecycle.toml"))
    if len(lifecycle_files) != 1:
        message = f"expected one rendered lifecycle under {output_dir}, found {len(lifecycle_files)}"
        raise AssertionError(message)

    lifecycle_path = lifecycle_files[0]
    with lifecycle_path.open("rb") as stream:
        lifecycle = tomllib.load(stream)

    if lifecycle.get("version") != 1:
        message = f"{lifecycle_path} is not lifecycle v1"
        raise AssertionError(message)
    if lifecycle.get("template") != expected_template:
        message = f"{lifecycle_path} records template {lifecycle.get('template')!r}, expected {expected_template!r}"
        raise AssertionError(message)
    if not isinstance(lifecycle.get("name"), str) or not lifecycle["name"]:
        message = f"{lifecycle_path} has no project name"
        raise AssertionError(message)
    processes = lifecycle.get("processes")
    if not isinstance(processes, dict) or not processes:
        message = f"{lifecycle_path} has no v1 processes"
        raise AssertionError(message)
    for process_id, process in processes.items():
        if not isinstance(process, dict) or not isinstance(process.get("command"), list) or not process["command"]:
            message = f"{lifecycle_path} process {process_id!r} has no command"
            raise AssertionError(message)
    forbidden = {"actions", "references", "visibility"}.intersection(lifecycle)
    if forbidden:
        message = f"{lifecycle_path} contains lifecycle-v2 sections: {sorted(forbidden)}"
        raise AssertionError(message)


def _assert_listing(output: str) -> None:
    missing = [template for template in REPRESENTATIVE_TEMPLATES if template not in output]
    if missing:
        message = f"installed template listing omitted: {', '.join(missing)}"
        raise AssertionError(message)


def _catalog_environment(work_root: Path, name: str) -> tuple[dict[str, str], Path]:
    state_root = work_root / name
    cache_root = state_root / "cookiecutter"
    state_root.mkdir(parents=True, exist_ok=True)
    config_path = state_root / "cookiecutter.yaml"
    config_path.write_text(
        f"cookiecutters_dir: {cache_root}\nreplay_dir: {state_root / 'replay'}\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["COOKIECUTTER_CONFIG"] = str(config_path)
    return env, cache_root


def _render_phase(
    command: list[str],
    *,
    env: dict[str, str],
    output_root: Path,
    checkout: str | None = None,
    explicit_repository: bool = False,
) -> None:
    for template in REPRESENTATIVE_TEMPLATES:
        output_dir = output_root / template.replace("/", "-")
        output_dir.mkdir(parents=True)
        if explicit_repository:
            create_command = [
                *command,
                CORE_REPOSITORY,
                "--template",
                f"templates/{template}",
                "--no-input",
            ]
        else:
            create_command = [*command, template, "--no-input"]
        if checkout is not None:
            create_command.extend(("--checkout", checkout))
        _run(create_command, cwd=output_dir, env=env)
        _assert_v1_lifecycle(output_dir, template)


def _assert_cache_commit(cache_root: Path, expected: str, *, cwd: Path, env: dict[str, str]) -> None:
    cached_repository = cache_root / "agentseek"
    actual = _run(
        ["git", "-C", str(cached_repository), "rev-parse", "HEAD"],
        cwd=cwd,
        env=env,
    ).strip()
    if actual != expected:
        message = f"cached template repository resolved {actual!r}, expected candidate {expected!r}"
        raise AssertionError(message)


def _with_checkout(command: list[str], checkout: str | None) -> list[str]:
    return [*command] if checkout is None else [*command, "--checkout", checkout]


def _assert_candidate_cache(
    cache_root: Path,
    candidate_ref: str | None,
    *,
    cwd: Path,
    env: dict[str, str],
) -> None:
    if candidate_ref is not None:
        _assert_cache_commit(cache_root, candidate_ref, cwd=cwd, env=env)


def verify_release(version: str, *, work_root: Path, candidate_ref: str | None = None) -> None:
    case = CASES[version]
    uvx = shutil.which("uvx")
    if uvx is None:
        message = "uvx is required"
        raise RuntimeError(message)

    command = [uvx, "--from", f"{case.distribution}=={version}", "agentseek", "create"]
    listing_env, listing_cache_root = _catalog_environment(work_root, "listing-state")
    render_env, render_cache_root = _catalog_environment(work_root, "render-state")

    if case.generation == "cookiecutter":
        listing = _run([*command, "--list-templates"], cwd=work_root, env=listing_env)
        if "No templates found" not in listing:
            message = f"AgentSeek {version} installed listing behavior changed"
            raise AssertionError(message)
        _render_phase(
            command,
            env=render_env,
            output_root=work_root / "rendered-cold",
            checkout=candidate_ref,
            explicit_repository=candidate_ref is not None,
        )
        _assert_candidate_cache(render_cache_root, candidate_ref, cwd=work_root, env=render_env)
        return

    cold_listing_command = _with_checkout([*command, "--template"], candidate_ref)
    cold_listing = _run(cold_listing_command, cwd=work_root, env=listing_env)
    _assert_listing(cold_listing)
    _assert_candidate_cache(listing_cache_root, candidate_ref, cwd=work_root, env=listing_env)

    _render_phase(
        command,
        env=render_env,
        output_root=work_root / "rendered-cold",
        checkout=candidate_ref,
    )
    _assert_candidate_cache(render_cache_root, candidate_ref, cwd=work_root, env=render_env)
    warm_listing = _run([*command, "--template"], cwd=work_root, env=render_env)
    _assert_listing(warm_listing)
    _render_phase(command, env=render_env, output_root=work_root / "rendered-warm")
    _assert_candidate_cache(render_cache_root, candidate_ref, cwd=work_root, env=render_env)

    if case.generation != "repairing":
        return

    cached_index = render_cache_root / "agentseek" / "templates" / "index.json"
    if not cached_index.is_file():
        message = f"AgentSeek {version} did not populate the expected cache"
        raise AssertionError(message)
    cached_index.unlink()
    repaired_listing_command = _with_checkout([*command, "--template"], candidate_ref)
    repaired_listing = _run(repaired_listing_command, cwd=work_root, env=render_env)
    _assert_listing(repaired_listing)
    if not cached_index.is_file():
        message = f"AgentSeek {version} did not repair its incomplete cache"
        raise AssertionError(message)
    _assert_candidate_cache(render_cache_root, candidate_ref, cwd=work_root, env=render_env)
    _render_phase(command, env=render_env, output_root=work_root / "rendered-repaired")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("version", choices=tuple(CASES))
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--candidate-ref", help="Exact core commit to exercise before it reaches the default branch.")
    args = parser.parse_args()

    if args.candidate_ref is not None and (
        len(args.candidate_ref) != 40 or any(character not in "0123456789abcdef" for character in args.candidate_ref)
    ):
        parser.error("--candidate-ref must be a full lowercase commit SHA")

    if args.work_root is not None:
        args.work_root.mkdir(parents=True, exist_ok=True)
        verify_release(args.version, work_root=args.work_root.resolve(), candidate_ref=args.candidate_ref)
        return

    with tempfile.TemporaryDirectory(prefix=f"agentseek-{args.version}-compat-") as temporary:
        verify_release(args.version, work_root=Path(temporary), candidate_ref=args.candidate_ref)


if __name__ == "__main__":
    main()
