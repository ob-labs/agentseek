"""JSON-safe diagnostics over normalized lifecycle inputs."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any, Literal, cast

import httpx
from pydantic import Field, create_model
from pydantic_settings import BaseSettings, SettingsConfigDict

from agentseek.cli.lifecycle.discovery import (
    EnvironmentDiagnosticSource,
    HttpDiagnosticSource,
    NormalizedLifecycleProject,
    PathDiagnosticSource,
    ToolDiagnosticSource,
)
from agentseek.cli.lifecycle.json_output import CheckResultDTO, DoctorDataDTO, WarningDTO
from agentseek.cli.lifecycle.safety import resolve_confined_project_path
from agentseek.cli.lifecycle.spec import LIFECYCLE_SPEC_FILE


def _environment_values(
    root: Path,
    env_file: PathDiagnosticSource | None,
    sources: tuple[EnvironmentDiagnosticSource, ...],
) -> dict[str, str]:
    """Read only declared environment names from shell and a safe env file."""

    class EnvironmentSettings(BaseSettings):
        model_config = SettingsConfigDict(extra="ignore", case_sensitive=True, env_ignore_empty=True)

    fields: dict[str, Any] = {}
    source_fields: dict[str, tuple[str, ...]] = {}
    for index, source in enumerate(sources):
        names: list[str] = []
        for key_index, key in enumerate((source.name, *source.aliases)):
            field_name = f"env_{index}_{key_index}"
            fields[field_name] = (str | None, Field(None, validation_alias=key))
            names.append(field_name)
        source_fields[source.name] = tuple(names)
    settings_type = cast(
        "type[BaseSettings]",
        create_model("JsonDiagnosticEnvironmentSettings", __base__=EnvironmentSettings, **fields),
    )
    safe_env_file: Path | None = None
    if env_file is not None and env_file.path is not None:
        safe_env_file = resolve_confined_project_path(root, env_file.path.path)
    settings = settings_type(_env_file=safe_env_file).model_dump(exclude_none=True)
    return {
        source.name: next(
            (str(settings[field_name]) for field_name in source_fields[source.name] if settings.get(field_name)),
            "",
        )
        for source in sources
    }


def _environment_result(source: EnvironmentDiagnosticSource, values: dict[str, str]) -> CheckResultDTO:
    keys = (source.name, *source.aliases)
    configured = bool(values.get(source.name)) or source.has_usable_default
    label = " or ".join(keys)
    state = "pass" if configured or not source.required else "fail"
    if configured:
        message = f"{label} is configured."
    elif source.required:
        message = f"{label} is not configured."
    else:
        message = f"{label} is optional and not configured."
    return CheckResultDTO(
        id=source.id,
        scope="project",
        service_id=None,
        type="env",
        state=state,
        message=message,
        target=source.name,
    )


def _tool_result(source: ToolDiagnosticSource) -> CheckResultDTO:
    if source.tool is None:
        return CheckResultDTO(
            id=source.id,
            scope="project",
            service_id=None,
            type="tool",
            state="fail",
            message="Unsafe executable requirement was not checked.",
            target=None,
        )
    tool = source.tool.name
    available = shutil.which(tool) is not None
    return CheckResultDTO(
        id=source.id,
        scope="project",
        service_id=None,
        type="tool",
        state="pass" if available else "fail",
        message=f"{tool} is {'available' if available else 'missing'}.",
        target=tool,
    )


def _path_result(
    root: Path,
    source: PathDiagnosticSource,
    *,
    result_type: Literal["path", "env_file"],
) -> CheckResultDTO:
    if source.path is None:
        return CheckResultDTO(
            id=source.id,
            scope="project",
            service_id=None,
            type=result_type,
            state="fail",
            message="Unsafe project path was not checked.",
            target=None,
        )
    path = source.path.path
    resolved = resolve_confined_project_path(root, path)
    present = resolved.is_file() if result_type == "env_file" else resolved.exists()
    return CheckResultDTO(
        id=source.id,
        scope="project",
        service_id=None,
        type=result_type,
        state="pass" if present else "fail",
        message=f"{path} is {'present' if present else 'missing'}.",
        target=path,
    )


def _process_cwd_result(root: Path, source: PathDiagnosticSource) -> CheckResultDTO:
    if source.path is None:
        return CheckResultDTO(
            id=source.id,
            scope="project",
            service_id=None,
            type="process_cwd",
            state="fail",
            message="Unsafe project path was not checked.",
            target=None,
        )
    path = source.path.path
    present = resolve_confined_project_path(root, path, allow_dot=True).is_dir()
    return CheckResultDTO(
        id=source.id,
        scope="project",
        service_id=None,
        type="process_cwd",
        state="pass" if present else "fail",
        message=f"{path} is {'present' if present else 'missing'}.",
        target=path,
    )


def _http_result(source: HttpDiagnosticSource, *, live: bool) -> CheckResultDTO:
    scope = "service" if source.service_id is not None else "project"
    if not live:
        return CheckResultDTO(
            id=source.id,
            scope=scope,
            service_id=source.service_id,
            type="http",
            state="not_run",
            message="Live check was not requested.",
            target=source.target,
        )
    if source.target is None:
        return CheckResultDTO(
            id=source.id,
            scope=scope,
            service_id=source.service_id,
            type="http",
            state="fail",
            message="Unsafe endpoint was not checked.",
            target=None,
        )
    reachable = False
    attempts = max(source.attempts, 1)
    for attempt in range(attempts):
        try:
            response = httpx.get(source.target, timeout=source.timeout)
            reachable = 200 <= response.status_code < 400
        except (httpx.HTTPError, ValueError, OverflowError):
            reachable = False
        if reachable:
            break
        if attempt + 1 < attempts:
            time.sleep(0.2)
    return CheckResultDTO(
        id=source.id,
        scope=scope,
        service_id=source.service_id,
        type="http",
        state="pass" if reachable else "fail",
        message=f"{source.target} is {'reachable' if reachable else 'not reachable'}.",
        target=source.target,
    )


def evaluate_doctor_json(root: Path, project: NormalizedLifecycleProject, *, live: bool) -> DoctorDataDTO:
    """Capture one deterministic diagnostic snapshot from normalized safe inputs."""
    environment_values = _environment_values(
        root,
        project.diagnostic_inputs.env_file,
        project.diagnostic_inputs.environment,
    )
    results = [
        CheckResultDTO(
            id="lifecycle:spec",
            scope="project",
            service_id=None,
            type="lifecycle",
            state="pass",
            message="Lifecycle spec is present.",
            target=LIFECYCLE_SPEC_FILE,
        ),
        *(
            [_path_result(root, project.diagnostic_inputs.env_file, result_type="env_file")]
            if project.diagnostic_inputs.env_file is not None
            else []
        ),
        *(_tool_result(source) for source in project.diagnostic_inputs.tools),
        *(_path_result(root, source, result_type="path") for source in project.diagnostic_inputs.required_paths),
        *(_environment_result(source, environment_values) for source in project.diagnostic_inputs.environment),
        *(_process_cwd_result(root, source) for source in project.diagnostic_inputs.process_cwds),
        *(_http_result(source, live=live) for source in project.diagnostic_inputs.http_checks),
    ]
    results.sort(key=lambda result: result.id)
    return DoctorDataDTO(
        passed=not any(result.state == "fail" for result in results),
        live_requested=live,
        results=tuple(results),
        warnings=tuple(WarningDTO.from_normalized(warning) for warning in project.warnings),
    )


__all__ = ["evaluate_doctor_json"]
