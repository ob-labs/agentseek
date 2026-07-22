"""Safe, deterministic lifecycle discovery normalization."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from agentseek.cli.lifecycle.authored import AuthoredLifecycleSpec, LifecycleSpecV1, LifecycleSpecV2
from agentseek.cli.lifecycle.discovery import (
    DiagnosticInputs,
    EnvironmentDiagnosticSource,
    HttpDiagnosticSource,
    NormalizationWarning,
    NormalizedCheckDefinition,
    NormalizedEnvironmentRequirement,
    NormalizedLifecycleProject,
    NormalizedProject,
    NormalizedService,
    NormalizedTask,
    PathDiagnosticSource,
    SafeExecutableName,
    SafeProjectPath,
    ToolDiagnosticSource,
)
from agentseek.cli.lifecycle.safety import (
    UnsafeProjectPathError,
    resolve_confined_project_path,
    safe_v1_endpoint,
    validate_bare_executable,
)


def _nullable_string(value: str) -> str | None:
    """Map authored empty text to the normalized null representation."""
    return value or None


def _first_occurrences(values: Iterable[str]) -> tuple[tuple[str, int], ...]:
    """Return one entry per literal value, retaining its original position."""
    seen: set[str] = set()
    collapsed: list[tuple[str, int]] = []
    for index, value in enumerate(values):
        if value in seen:
            continue
        seen.add(value)
        collapsed.append((value, index))
    return tuple(collapsed)


def _safe_project_path(project_root: Path, value: str, *, allow_dot: bool = False) -> SafeProjectPath | None:
    """Keep a relative path only after confinement validation succeeds."""
    try:
        resolve_confined_project_path(project_root, value, allow_dot=allow_dot)
    except UnsafeProjectPathError:
        return None
    return SafeProjectPath(path=value)


def _metadata_incomplete_warning() -> NormalizationWarning:
    return NormalizationWarning(
        code="lifecycle_v1_metadata_incomplete",
        message="Lifecycle v1 metadata is incomplete.",
        details={},
    )


def _normalize_v1(spec: LifecycleSpecV1, *, project_root: Path) -> NormalizedLifecycleProject:
    environment = tuple(
        NormalizedEnvironmentRequirement(
            name=name,
            required=requirement.required,
            description=_nullable_string(requirement.description),
            aliases=tuple(sorted(requirement.aliases)),
        )
        for name, requirement in sorted(spec.env.items())
    )
    services = tuple(
        NormalizedService(
            id=service_id,
            name=None,
            description=None,
            url=safe_v1_endpoint(service.url),
            kind=None,
            display=None,
            primary=None,
            tech=None,
        )
        for service_id, service in sorted(spec.services.items())
    )
    checks = tuple(
        NormalizedCheckDefinition(
            id=check_id,
            service_id=None,
            target=safe_v1_endpoint(check.target, http_only=True),
        )
        for check_id, check in sorted(spec.checks.items())
    )
    tasks = tuple(
        NormalizedTask(id=task_id, description=_nullable_string(task.description))
        for task_id, task in sorted(spec.tasks.items())
    )

    env_file = (
        _safe_project_path(project_root, spec.env_file)
        if spec.env_file is not None
        else None
    )
    process_cwds = tuple(
        PathDiagnosticSource(
            id=f"process-cwd:{process_id}",
            owner_id=process_id,
            path=path,
        )
        for process_id, process in sorted(spec.processes.items())
        if (path := _safe_project_path(project_root, process.cwd, allow_dot=True)) is not None
    )

    tools = tuple(
        ToolDiagnosticSource(id=f"tool:{tool}", tool=SafeExecutableName(name=tool))
        for tool, _ in sorted(_first_occurrences(spec.required_tools))
        if _is_safe_executable(tool)
    )
    required_paths = tuple(
        PathDiagnosticSource(id=f"path:{value}", path=path)
        for value, _ in sorted(_first_occurrences(spec.required_paths))
        if (path := _safe_project_path(project_root, value)) is not None
    )
    diagnostic_inputs = DiagnosticInputs(
        env_file=(
            PathDiagnosticSource(id=f"env-file:{spec.env_file}", path=env_file)
            if env_file is not None and spec.env_file is not None
            else None
        ),
        tools=tools,
        required_paths=required_paths,
        process_cwds=process_cwds,
        environment=tuple(
            EnvironmentDiagnosticSource(
                id=f"env:{name}",
                name=name,
                aliases=tuple(sorted(requirement.aliases)),
                required=requirement.required,
                has_usable_default=bool(requirement.default),
            )
            for name, requirement in sorted(spec.env.items())
        ),
        http_checks=tuple(
            HttpDiagnosticSource(
                id=f"service-check:{check_id}",
                service_id=None,
                target=safe_v1_endpoint(check.target, http_only=True),
                timeout=check.timeout,
                attempts=check.attempts,
            )
            for check_id, check in sorted(spec.checks.items())
        ),
    )
    return NormalizedLifecycleProject(
        lifecycle_version=1,
        project=NormalizedProject(
            template=_nullable_string(spec.template),
            name=spec.name,
            description=None,
            guide=None,
        ),
        metadata_complete=False,
        environment=environment,
        services=services,
        checks=checks,
        tasks=tasks,
        actions=(),
        warnings=(_metadata_incomplete_warning(),),
        diagnostic_inputs=diagnostic_inputs,
    )


def _is_safe_executable(value: str) -> bool:
    try:
        validate_bare_executable(value)
    except ValueError:
        return False
    return True


def normalize_lifecycle(
    spec: AuthoredLifecycleSpec,
    *,
    project_root: Path,
) -> NormalizedLifecycleProject:
    """Project an already validated lifecycle spec into safe discovery metadata."""
    if isinstance(spec, LifecycleSpecV1):
        return _normalize_v1(spec, project_root=project_root)
    if isinstance(spec, LifecycleSpecV2):
        raise NotImplementedError
    raise TypeError


__all__ = ["normalize_lifecycle"]
