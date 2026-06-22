from __future__ import annotations

import contextlib
import os
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from duty import duty

AGENTSEEK = {
    "version": 1,
    "template": "bub/default",
}

PROJECT_NAME = "{{ cookiecutter.project_name }}"
PROJECT_SLUG = "{{ cookiecutter.project_slug }}"
DEFAULT_MODEL = "{{ cookiecutter.default_model }}"
GATEWAY_PORT = {{ cookiecutter.gateway_port }}
FRONTEND_PORT = {{ cookiecutter.frontend_port }}
COPILOTKIT_PORT = {{ cookiecutter.copilotkit_port }}
APP_URL = f"http://127.0.0.1:{FRONTEND_PORT}"
DEFAULT_AGENT_URL = f"http://127.0.0.1:{GATEWAY_PORT}/agent"
SHUTDOWN_GRACE_SECONDS = 10


@dataclass(frozen=True)
class Check:
    status: str
    name: str
    detail: str
    fix: str = ""


def _root() -> Path:
    return Path(__file__).resolve().parent


def _frontend_dir(root: Path) -> Path:
    return root / "frontend"


def _env_values(root: Path) -> dict[str, str]:
    env_path = root / ".env"
    values: dict[str, str] = {}
    if not env_path.is_file():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _model_provider(model: str) -> str:
    provider, separator, _model_name = model.partition(":")
    return provider.upper() if separator and provider else ""


def _api_key_configured(env: dict[str, str]) -> bool:
    provider = _model_provider(env.get("BUB_MODEL", DEFAULT_MODEL))
    provider_key = f"BUB_{provider}_API_KEY" if provider else ""
    return bool(env.get("BUB_API_KEY") or (provider_key and env.get(provider_key)))


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) != 0


def _require_binary(name: str) -> str:
    resolved = shutil.which(name)
    if resolved is None:
        print(f"Required executable {name!r} was not found on PATH.", file=sys.stderr)
        raise SystemExit(2)
    return resolved


def _build_env(root: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("BUB_STREAM_OUTPUT", "true")
    env.setdefault("BUB_AG_UI_PORT", str(GATEWAY_PORT))
    env.setdefault("FRONTEND_PORT", str(FRONTEND_PORT))
    env.setdefault("COPILOTKIT_PORT", str(COPILOTKIT_PORT))
    env.setdefault("BUB_AG_UI_AGENT_URL", DEFAULT_AGENT_URL)
    env.setdefault("VITE_BUB_AG_UI_URL", f"http://127.0.0.1:{GATEWAY_PORT}")
    env.setdefault("PWD", str(root))
    return env


def _spawn(cmd: list[str], *, cwd: Path, env: Mapping[str, str]) -> subprocess.Popen[bytes]:
    rendered = " ".join(shlex.quote(part) for part in cmd)
    print(f"$ {rendered}")
    return subprocess.Popen(  # noqa: S603
        cmd,
        cwd=str(cwd),
        env=dict(env),
        start_new_session=True,
    )


def _terminate(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    deadline = time.monotonic() + SHUTDOWN_GRACE_SECONDS
    while proc.poll() is None and time.monotonic() < deadline:
        time.sleep(0.2)
    if proc.poll() is None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(proc.pid, signal.SIGKILL)


def _validate_frontend(frontend_dir: Path) -> None:
    if not (frontend_dir / "package.json").is_file():
        print(f"Missing frontend package.json at {frontend_dir}.", file=sys.stderr)
        raise SystemExit(2)
    if not (frontend_dir / "node_modules").is_dir():
        print("Frontend dependencies are missing. Run `npm install --prefix frontend` first.", file=sys.stderr)
        raise SystemExit(2)


def _check(status: str, name: str, detail: str, fix: str = "") -> Check:
    return Check(status=status, name=name, detail=detail, fix=fix)


def _checks(*, live: bool) -> list[Check]:
    root = _root()
    frontend = root / "frontend"
    env = _env_values(root)
    api_key_name = f"BUB_{_model_provider(env.get('BUB_MODEL', DEFAULT_MODEL))}_API_KEY"
    checks = [
        _check("ok" if (root / "duties.py").is_file() else "fail", "duties.py", "Lifecycle file is present."),
        _check("ok" if (root / "pyproject.toml").is_file() else "fail", "pyproject.toml", "Python project file is present."),
        _check("ok" if shutil.which("uv") else "fail", "uv", "uv is available.", "Install uv: https://docs.astral.sh/uv/"),
        _check("ok" if shutil.which("node") else "fail", "node", "Node.js is available.", "Install Node.js."),
        _check("ok" if shutil.which("npm") else "fail", "npm", "npm is available.", "Install npm with Node.js."),
        _check(
            "ok" if (root / ".env").is_file() else "fail",
            ".env",
            ".env is present.",
            "Run `cp .env.example .env` and fill in model credentials.",
        ),
        _check(
            "ok" if env.get("BUB_MODEL") else "fail",
            "BUB_MODEL",
            "Bub model id is configured.",
            "Set BUB_MODEL in .env.",
        ),
        _check(
            "ok" if _api_key_configured(env) else "fail",
            "BUB_API_KEY",
            "Model provider key is configured.",
            f"Set BUB_API_KEY or {api_key_name} in .env.",
        ),
        _check(
            "ok" if (frontend / "package.json").is_file() else "fail",
            "frontend/package.json",
            "Frontend package file is present.",
        ),
        _check(
            "ok" if (frontend / "node_modules").is_dir() else "fail",
            "frontend/node_modules",
            "Frontend dependencies are installed.",
            "Run `npm install --prefix frontend`.",
        ),
    ]
    for port, name in (
        (GATEWAY_PORT, "gateway port"),
        (FRONTEND_PORT, "frontend port"),
        (COPILOTKIT_PORT, "copilotkit port"),
    ):
        port_available = _port_available(port)
        if live:
            status = "fail" if port_available else "ok"
            detail = f"Port {port} {'is not listening' if port_available else 'is listening'}."
            fix = "Start the local app with `uvx agentseek dev` before running live checks."
        else:
            status = "ok" if port_available else "fail"
            detail = f"Port {port} {'is available' if port_available else 'is already in use'}."
            fix = f"Stop the process using port {port} or change the template port."
        checks.append(_check(status, name, detail, fix))
    return checks


def _print_checks(checks: list[Check]) -> None:
    for item in checks:
        print(f"{item.status:<4} {item.name}: {item.detail}")
        if item.status in {"fail", "warn"} and item.fix:
            print(f"     next: {item.fix}")


@duty
def info(ctx, verbose: bool = False):
    """Print project summary."""
    del ctx
    root = _root()
    env = _env_values(root)
    print("Project")
    print(f"  Root: {root}")
    print(f"  Name: {PROJECT_NAME}")
    print(f"  Template: {AGENTSEEK['template']}")
    print(f"  Lifecycle: duties.py / AGENTSEEK version {AGENTSEEK['version']}")
    print()
    print("Entrypoints")
    print("  Dev: uvx agentseek dev")
    print(f"  App: {APP_URL}")
    print(f"  Gateway: http://127.0.0.1:{GATEWAY_PORT}/agent")
    print()
    print("Environment")
    print(f"  .env: {'present' if (root / '.env').is_file() else 'missing'}")
    print(f"  BUB_MODEL: {'set' if env.get('BUB_MODEL') else 'missing'}")
    print(f"  BUB_API_KEY: {'set' if _api_key_configured(env) else 'missing'}")
    print()
    print("Next")
    print("  uvx agentseek doctor")
    print("  uvx agentseek dev")
    if verbose:
        print()
        print("Discovery")
        print(f"  Python: {sys.executable}")
        print(f"  uv: {shutil.which('uv') or 'missing'}")
        print(f"  npm: {shutil.which('npm') or 'missing'}")


@duty
def doctor(ctx, live: bool = False, strict: bool = False):
    """Check local project readiness."""
    del ctx
    checks = _checks(live=live)
    _print_checks(checks)
    has_fail = any(item.status == "fail" for item in checks)
    has_warn = any(item.status == "warn" for item in checks)
    if has_fail or (strict and has_warn):
        raise SystemExit(1)


@duty(capture=False)
def dev(ctx, dry_run: bool = False):
    """Run the local app."""
    del ctx
    root = _root()
    print("Startup plan")
    print("  Gateway: uv run bub gateway --enable-channel ag-ui")
    print("  Frontend: npm run dev")
    print(f"  App: {APP_URL}")
    print(f"  Gateway: http://127.0.0.1:{GATEWAY_PORT}/agent")
    if dry_run:
        return

    frontend_dir = _frontend_dir(root)
    _validate_frontend(frontend_dir)

    env = _build_env(root)
    uv = _require_binary("uv")
    npm = _require_binary("npm")
    gateway = _spawn([uv, "run", "bub", "gateway", "--enable-channel", "ag-ui"], cwd=root, env=env)
    frontend = _spawn([npm, "run", "dev"], cwd=frontend_dir, env=env)

    def _shutdown(*_args: object) -> None:
        _terminate(frontend)
        _terminate(gateway)
        raise SystemExit(0)

    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, _shutdown)

    try:
        while True:
            gateway_code = gateway.poll()
            frontend_code = frontend.poll()
            if gateway_code is not None or frontend_code is not None:
                _terminate(frontend)
                _terminate(gateway)
                raise SystemExit(gateway_code or frontend_code or 0)
            time.sleep(1.0)
    finally:
        _terminate(frontend)
        _terminate(gateway)
