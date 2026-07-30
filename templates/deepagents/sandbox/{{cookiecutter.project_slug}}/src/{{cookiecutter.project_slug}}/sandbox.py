"""Sandbox provider selection for the DeepAgents coding agent."""

from __future__ import annotations

import os
import posixpath
import shlex
import threading
import warnings
from collections.abc import Callable
from typing import Any

SUPPORTED_SANDBOX_PROVIDERS = {"daytona", "langsmith"}


def _workspace_path(workspace: str, path: str) -> str:
    """Map a DeepAgents logical path into a sandbox's writable workspace."""
    if not path:
        return workspace
    normalized_workspace = posixpath.normpath(workspace)
    normalized_path = posixpath.normpath(path)
    if normalized_path == normalized_workspace or normalized_path.startswith(
        normalized_workspace + "/"
    ):
        return normalized_path
    candidate = posixpath.normpath(
        posixpath.join(normalized_workspace, normalized_path.lstrip("/"))
    )
    if candidate != normalized_workspace and not candidate.startswith(normalized_workspace + "/"):
        raise ValueError("Sandbox file paths must remain inside the writable workspace.")
    return candidate


def _daytona_backend_with_workspace(sandbox: Any, workspace: str) -> Any:
    """Create a Daytona backend whose logical root is its writable work directory."""
    from langchain_daytona import DaytonaSandbox

    class WorkspaceDaytonaSandbox(DaytonaSandbox):
        def __init__(self, *, sandbox: Any, workspace: str) -> None:
            super().__init__(sandbox=sandbox)
            self.workspace = posixpath.normpath(workspace)

        def _resolve_path(self, path: str) -> str:
            return _workspace_path(self.workspace, path)

        def _logical_path(self, path: str | None) -> str | None:
            if path is None:
                return None
            if path == self.workspace:
                return "/"
            if path.startswith(self.workspace + "/"):
                return "/" + path.removeprefix(self.workspace + "/")
            return path

        def _logicalize_result_paths(
            self,
            result: Any,
            attribute: str,
            *,
            base_path: str | None = None,
        ) -> Any:
            for item in getattr(result, attribute, None) or []:
                item_path = item.get("path")
                if item_path is not None and base_path is not None and not posixpath.isabs(item_path):
                    item_path = posixpath.normpath(posixpath.join(base_path, item_path))
                    if item_path != self.workspace and not item_path.startswith(self.workspace + "/"):
                        raise ValueError(
                            "Sandbox file paths must remain inside the writable workspace."
                        )
                item["path"] = self._logical_path(item_path)
            return result

        def execute(self, command: str, *, timeout: int | None = None) -> Any:
            command_in_workspace = f"cd {shlex.quote(self.workspace)} && {command}"
            if timeout is None:
                return super().execute(command_in_workspace)
            return super().execute(command_in_workspace, timeout=timeout)

        def upload_files(self, files: list[tuple[str, bytes]]) -> Any:
            responses = super().upload_files(
                [(self._resolve_path(path), content) for path, content in files]
            )
            for response in responses:
                response.path = self._logical_path(response.path)
            return responses

        def download_files(self, paths: list[str]) -> Any:
            responses = super().download_files([self._resolve_path(path) for path in paths])
            for response in responses:
                response.path = self._logical_path(response.path)
            return responses

        def ls(self, path: str) -> Any:
            result = super().ls(self._resolve_path(path))
            return self._logicalize_result_paths(result, "entries")

        async def als(self, path: str) -> Any:
            result = await super().als(self._resolve_path(path))
            return self._logicalize_result_paths(result, "entries")

        def read(self, file_path: str, offset: int = 0, limit: int = 2000) -> Any:
            return super().read(self._resolve_path(file_path), offset, limit)

        async def aread(self, file_path: str, offset: int = 0, limit: int = 2000) -> Any:
            return await super().aread(self._resolve_path(file_path), offset, limit)

        def write(self, file_path: str, content: str) -> Any:
            result = super().write(self._resolve_path(file_path), content)
            result.path = self._logical_path(result.path)
            return result

        async def awrite(self, file_path: str, content: str) -> Any:
            result = await super().awrite(self._resolve_path(file_path), content)
            result.path = self._logical_path(result.path)
            return result

        def edit(
            self,
            file_path: str,
            old_string: str,
            new_string: str,
            replace_all: bool = False,
        ) -> Any:
            result = super().edit(
                self._resolve_path(file_path), old_string, new_string, replace_all
            )
            result.path = self._logical_path(result.path)
            return result

        async def aedit(
            self,
            file_path: str,
            old_string: str,
            new_string: str,
            replace_all: bool = False,
        ) -> Any:
            result = await super().aedit(
                self._resolve_path(file_path), old_string, new_string, replace_all
            )
            result.path = self._logical_path(result.path)
            return result

        def glob(self, pattern: str, path: str | None = None) -> Any:
            base_path = self._resolve_path(path or "/")
            result = super().glob(pattern, base_path)
            return self._logicalize_result_paths(result, "matches", base_path=base_path)

        async def aglob(self, pattern: str, path: str | None = None) -> Any:
            base_path = self._resolve_path(path or "/")
            result = await super().aglob(pattern, base_path)
            return self._logicalize_result_paths(result, "matches", base_path=base_path)

        def grep(
            self,
            pattern: str,
            path: str | None = None,
            glob: str | None = None,
        ) -> Any:
            result = super().grep(
                pattern,
                self._resolve_path(path or "/"),
                glob,
            )
            return self._logicalize_result_paths(result, "matches")

        async def agrep(
            self,
            pattern: str,
            path: str | None = None,
            glob: str | None = None,
        ) -> Any:
            result = await super().agrep(
                pattern,
                self._resolve_path(path or "/"),
                glob,
            )
            return self._logicalize_result_paths(result, "matches")

    return WorkspaceDaytonaSandbox(sandbox=sandbox, workspace=workspace)


def _nonempty_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def normalize_sandbox_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized in SUPPORTED_SANDBOX_PROVIDERS:
        return normalized
    supported = ", ".join(sorted(SUPPORTED_SANDBOX_PROVIDERS))
    raise ValueError(
        f"Unsupported AGENTSEEK_SANDBOX_PROVIDER={provider!r}. Expected one of: {supported}."
    )


def _sandbox_identifier(sandbox: Any, attribute: str) -> str:
    value = getattr(sandbox, attribute, None)
    if isinstance(value, (str, int)) and str(value):
        return str(value)
    return "unknown"


def _best_effort_cleanup(
    action: Callable[[], None], *, provider: str, sandbox_id: str
) -> Callable[[], None]:
    lock = threading.Lock()
    attempted = False

    def cleanup() -> None:
        nonlocal attempted
        with lock:
            if attempted:
                return
            attempted = True
        try:
            action()
        except Exception:
            try:
                warnings.warn(
                    f"Failed to delete {provider} sandbox {sandbox_id!r}. "
                    "Delete it manually in the provider dashboard.",
                    RuntimeWarning,
                    stacklevel=2,
                )
            except RuntimeWarning:
                pass

    return cleanup


def create_sandbox_backend(provider: str | None = None) -> tuple[Any, Callable[[], None]]:
    selected = normalize_sandbox_provider(
        provider or os.getenv("AGENTSEEK_SANDBOX_PROVIDER") or "daytona"
    )
    if selected == "daytona":
        if not _nonempty_env("DAYTONA_API_KEY"):
            raise RuntimeError("DAYTONA_API_KEY is required when AGENTSEEK_SANDBOX_PROVIDER=daytona.")
        from daytona import Daytona

        client = Daytona()
        sandbox = client.create()
        cleanup = _best_effort_cleanup(
            lambda: client.delete(sandbox),
            provider="daytona",
            sandbox_id=_sandbox_identifier(sandbox, "id"),
        )
        try:
            backend = _daytona_backend_with_workspace(sandbox, sandbox.get_work_dir())
        except Exception:
            cleanup()
            raise
        return backend, cleanup

    if not _nonempty_env("LANGSMITH_API_KEY"):
        raise RuntimeError("LANGSMITH_API_KEY is required when AGENTSEEK_SANDBOX_PROVIDER=langsmith.")
    from deepagents.backends import LangSmithSandbox
    from langsmith.sandbox import SandboxClient

    client = SandboxClient()
    sandbox = client.create_sandbox()
    cleanup = _best_effort_cleanup(
        lambda: client.delete_sandbox(sandbox.name),
        provider="langsmith",
        sandbox_id=_sandbox_identifier(sandbox, "name"),
    )
    try:
        backend = LangSmithSandbox(sandbox=sandbox)
    except Exception:
        cleanup()
        raise
    return backend, cleanup
