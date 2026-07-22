"""Safe, deterministic lifecycle discovery normalization."""

from __future__ import annotations

import json
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
    NormalizedProjectFile,
    NormalizedReference,
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


def _duplicate_requirement_warnings(values: Iterable[str], *, requirement_type: str) -> tuple[NormalizationWarning, ...]:
    """Describe repeated requirement literals without retaining those literals."""
    first_indices: dict[str, int] = {}
    warnings: list[NormalizationWarning] = []
    for index, value in enumerate(values):
        first_index = first_indices.setdefault(value, index)
        if first_index != index:
            warnings.append(
                NormalizationWarning(
                    code="duplicate_requirement_collapsed",
                    message="Duplicate requirement was collapsed.",
                    details={
                        "requirement_type": requirement_type,
                        "first_index": first_index,
                        "duplicate_index": index,
                    },
                )
            )
    return tuple(warnings)


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


def _warning_sort_key(warning: NormalizationWarning) -> tuple[str, str, str]:
    """Return the normative, stable warning-array sort key."""
    return (
        warning.code,
        warning.message,
        json.dumps(warning.details, ensure_ascii=False, separators=(",", ":")),
    )


def _unsafe_endpoint_warning(*, owner_type: str, owner_id: str, field: str) -> NormalizationWarning:
    return NormalizationWarning(
        code="unsafe_endpoint_omitted",
        message="Unsafe endpoint was omitted.",
        details={"owner_type": owner_type, "owner_id": owner_id, "field": field},
    )


def _unsafe_path_warning(
    *,
    owner_type: str,
    owner_id: str | None,
    index: int | None,
    field: str,
) -> NormalizationWarning:
    return NormalizationWarning(
        code="unsafe_path_omitted",
        message="Unsafe project path was omitted.",
        details={"owner_type": owner_type, "owner_id": owner_id, "index": index, "field": field},
    )


def _v1_services_and_checks(
    spec: LifecycleSpecV1,
    warnings: list[NormalizationWarning],
) -> tuple[tuple[NormalizedService, ...], tuple[NormalizedCheckDefinition, ...], dict[str, str | None]]:
    services: list[NormalizedService] = []
    for service_id, service in sorted(spec.services.items()):
        url = safe_v1_endpoint(service.url)
        if url is None:
            warnings.append(_unsafe_endpoint_warning(owner_type="service", owner_id=service_id, field="url"))
        services.append(
            NormalizedService(
                id=service_id,
                name=None,
                description=None,
                url=url,
                kind=None,
                display=None,
                primary=None,
                tech=None,
            )
        )
    check_targets: dict[str, str | None] = {}
    checks: list[NormalizedCheckDefinition] = []
    for check_id, check in sorted(spec.checks.items()):
        target = safe_v1_endpoint(check.target, http_only=True)
        if target is None:
            warnings.append(_unsafe_endpoint_warning(owner_type="check", owner_id=check_id, field="target"))
        check_targets[check_id] = target
        checks.append(NormalizedCheckDefinition(id=check_id, service_id=None, target=target))
    return tuple(services), tuple(checks), check_targets


def _v1_path_diagnostic_sources(
    spec: LifecycleSpecV1,
    *,
    project_root: Path,
    warnings: list[NormalizationWarning],
) -> tuple[
    PathDiagnosticSource | None,
    tuple[ToolDiagnosticSource, ...],
    tuple[PathDiagnosticSource, ...],
    tuple[PathDiagnosticSource, ...],
]:
    env_file: PathDiagnosticSource | None = None
    if spec.env_file is not None:
        safe_env_file = _safe_project_path(project_root, spec.env_file)
        if safe_env_file is None:
            warnings.append(_unsafe_path_warning(owner_type="env_file", owner_id=None, index=None, field="env_file"))
            env_file = PathDiagnosticSource(id="unsafe-path:env-file", path=None)
        else:
            env_file = PathDiagnosticSource(id=f"env-file:{spec.env_file}", path=safe_env_file)

    process_cwds: list[PathDiagnosticSource] = []
    for sorted_index, (process_id, process) in enumerate(sorted(spec.processes.items())):
        path = _safe_project_path(project_root, process.cwd, allow_dot=True)
        if path is None:
            warnings.append(_unsafe_path_warning(owner_type="process", owner_id=process_id, index=None, field="cwd"))
            process_cwds.append(
                PathDiagnosticSource(
                    id=f"unsafe-path:process-cwd:{sorted_index}",
                    owner_id=process_id,
                    source_index=sorted_index,
                    path=None,
                )
            )
        else:
            process_cwds.append(PathDiagnosticSource(id=f"process-cwd:{process_id}", owner_id=process_id, path=path))

    tools, required_paths = _v1_requirement_sources(spec, project_root=project_root, warnings=warnings)

    for task_id, task in sorted(spec.tasks.items()):
        if _safe_project_path(project_root, task.cwd, allow_dot=True) is None:
            warnings.append(_unsafe_path_warning(owner_type="task", owner_id=task_id, index=None, field="cwd"))

    return (
        env_file,
        tuple(sorted(tools, key=lambda source: source.id)),
        tuple(sorted(required_paths, key=lambda source: source.id)),
        tuple(sorted(process_cwds, key=lambda source: source.id)),
    )


def _v1_requirement_sources(
    spec: LifecycleSpecV1,
    *,
    project_root: Path,
    warnings: list[NormalizationWarning],
) -> tuple[tuple[ToolDiagnosticSource, ...], tuple[PathDiagnosticSource, ...]]:
    tools: list[ToolDiagnosticSource] = []
    warnings.extend(_duplicate_requirement_warnings(spec.required_tools, requirement_type="tool"))
    for tool, authored_index in _first_occurrences(spec.required_tools):
        if _is_safe_executable(tool):
            tools.append(ToolDiagnosticSource(id=f"tool:{tool}", tool=SafeExecutableName(name=tool)))
        else:
            warnings.append(_unsafe_path_warning(owner_type="required_tool", owner_id=None, index=authored_index, field="tool"))
            tools.append(ToolDiagnosticSource(id=f"unsafe-path:required-tool:{authored_index}", source_index=authored_index, tool=None))

    required_paths: list[PathDiagnosticSource] = []
    warnings.extend(_duplicate_requirement_warnings(spec.required_paths, requirement_type="path"))
    for value, authored_index in _first_occurrences(spec.required_paths):
        path = _safe_project_path(project_root, value)
        if path is None:
            warnings.append(_unsafe_path_warning(owner_type="required_path", owner_id=None, index=authored_index, field="path"))
            required_paths.append(PathDiagnosticSource(id=f"unsafe-path:required:{authored_index}", source_index=authored_index, path=None))
        else:
            required_paths.append(PathDiagnosticSource(id=f"path:{value}", path=path))
    return tuple(sorted(tools, key=lambda source: source.id)), tuple(sorted(required_paths, key=lambda source: source.id))


def _v1_diagnostic_inputs(
    spec: LifecycleSpecV1,
    *,
    project_root: Path,
    check_targets: dict[str, str | None],
    warnings: list[NormalizationWarning],
) -> DiagnosticInputs:
    env_file, tools, required_paths, process_cwds = _v1_path_diagnostic_sources(
        spec,
        project_root=project_root,
        warnings=warnings,
    )
    return DiagnosticInputs(
        env_file=env_file,
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
                target=check_targets[check_id],
                timeout=check.timeout,
                attempts=check.attempts,
            )
            for check_id, check in sorted(spec.checks.items())
        ),
    )


def _normalize_v1(spec: LifecycleSpecV1, *, project_root: Path) -> NormalizedLifecycleProject:
    warnings: list[NormalizationWarning] = [_metadata_incomplete_warning()]
    services, checks, check_targets = _v1_services_and_checks(spec, warnings)
    diagnostic_inputs = _v1_diagnostic_inputs(
        spec,
        project_root=project_root,
        check_targets=check_targets,
        warnings=warnings,
    )
    environment = tuple(
        NormalizedEnvironmentRequirement(
            name=name,
            required=requirement.required,
            description=_nullable_string(requirement.description),
            aliases=tuple(sorted(requirement.aliases)),
        )
        for name, requirement in sorted(spec.env.items())
    )
    tasks = tuple(
        NormalizedTask(id=task_id, description=_nullable_string(task.description))
        for task_id, task in sorted(spec.tasks.items())
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
        warnings=tuple(sorted(warnings, key=_warning_sort_key)),
        diagnostic_inputs=diagnostic_inputs,
    )


def _normalize_v2(spec: LifecycleSpecV2, *, project_root: Path) -> NormalizedLifecycleProject:
    """Project validated v2 metadata without evaluating topology or commands."""
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
            name=service.name,
            description=service.description,
            url=service.url,
            kind=service.kind,
            display=service.display,
            primary=service.primary,
            tech=service.tech,
            links=tuple(
                NormalizedReference(rel=rel, url=url)
                for rel, url in sorted(service.links.items())
            ),
        )
        for service_id, service in sorted(spec.services.items())
    )
    checks = tuple(
        NormalizedCheckDefinition(
            id=check_id,
            service_id=None,
            type=check.type,
            target=check.target,
            state="not_run",
        )
        for check_id, check in sorted(spec.checks.items())
    )
    tasks = tuple(
        NormalizedTask(id=task_id, description=_nullable_string(task.description))
        for task_id, task in sorted(spec.tasks.items())
    )
    diagnostic_inputs = DiagnosticInputs(
        env_file=(
            PathDiagnosticSource(
                id=f"env-file:{spec.env_file}",
                path=SafeProjectPath(path=spec.env_file),
            )
            if spec.env_file is not None
            else None
        ),
        tools=tuple(
            ToolDiagnosticSource(id=f"tool:{tool}", tool=SafeExecutableName(name=tool))
            for tool in sorted(spec.required_tools)
        ),
        required_paths=tuple(
            PathDiagnosticSource(id=f"path:{path}", path=SafeProjectPath(path=path))
            for path in sorted(spec.required_paths)
        ),
        process_cwds=tuple(
            PathDiagnosticSource(
                id=f"process-cwd:{process_id}",
                owner_id=process_id,
                path=SafeProjectPath(path=process.cwd),
            )
            for process_id, process in sorted(spec.processes.items())
        ),
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
                target=check.target,
                timeout=check.timeout,
                attempts=check.attempts,
            )
            for check_id, check in sorted(spec.checks.items())
        ),
    )
    return NormalizedLifecycleProject(
        lifecycle_version=2,
        project=NormalizedProject(
            template=spec.template,
            name=spec.name,
            description=spec.description,
            guide=(NormalizedProjectFile(path=spec.guide) if spec.guide is not None else None),
        ),
        metadata_complete=True,
        environment=environment,
        services=services,
        checks=checks,
        tasks=tasks,
        actions=(),
        warnings=(),
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
        return _normalize_v2(spec, project_root=project_root)
    raise TypeError


__all__ = ["normalize_lifecycle"]
