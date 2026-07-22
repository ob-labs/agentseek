"""Frozen normalized lifecycle discovery models."""

from __future__ import annotations

import json
from collections.abc import Mapping
from copy import deepcopy
from types import MappingProxyType
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_serializer, field_validator, model_validator
from pydantic_core import PydanticCustomError

from agentseek.cli.lifecycle.safety import (
    ReferenceRel,
    ServiceKind,
    safe_v1_endpoint,
    validate_bare_executable,
    validate_check_target,
    validate_identifier,
    validate_project_relative_path,
    validate_reference_url,
    validate_service_url,
)

ServiceDisplay = Literal["default", "advanced", "hidden"]
ProviderType = Literal["dev", "task"]
ActionType = Literal["open_url", "copy_endpoint", "open_reference", "start_dev", "run_task"]
WarningCode = Literal[
    "lifecycle_v1_metadata_incomplete",
    "unsafe_endpoint_omitted",
    "unsafe_path_omitted",
    "duplicate_requirement_collapsed",
]
WarningScalar = str | int | None


class SafeModel(BaseModel):
    """Immutable model base for normalized, safe lifecycle data."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class NormalizedProjectFile(SafeModel):
    path: str
    rel: Literal["guide"] = "guide"

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        try:
            return validate_project_relative_path(value)
        except ValueError:
            raise PydanticCustomError("unsafe_normalized_path", "normalized path is unsafe") from None


class NormalizedProject(SafeModel):
    template: str | None
    name: str
    description: str | None
    guide: NormalizedProjectFile | None


class NormalizedEnvironmentRequirement(SafeModel):
    name: str
    required: bool
    description: str | None
    aliases: tuple[str, ...] = ()


class NormalizedProvider(SafeModel):
    type: ProviderType
    id: str
    process_id: str | None = None
    task_id: str | None = None

    @model_validator(mode="after")
    def _validate_relationship(self) -> NormalizedProvider:
        if self.type == "dev":
            is_valid = self.process_id is not None and self.task_id is None and self.id == f"process:{self.process_id}"
        else:
            is_valid = self.task_id is not None and self.process_id is None and self.id == f"task:{self.task_id}"
        if not is_valid:
            raise PydanticCustomError("invalid_provider_relationship", "provider relationship is invalid")
        return self


class NormalizedReference(SafeModel):
    rel: ReferenceRel
    url: str

    @field_validator("url")
    @classmethod
    def _validate_url(cls, value: str, info: ValidationInfo) -> str:
        rel = info.data.get("rel")
        if rel is None:
            return value
        try:
            return validate_reference_url(rel, value)
        except ValueError:
            raise PydanticCustomError("unsafe_normalized_url", "normalized URL is unsafe") from None


class NormalizedService(SafeModel):
    id: str
    name: str | None
    description: str | None
    url: str | None
    kind: ServiceKind | None
    display: ServiceDisplay | None
    primary: bool | None
    tech: str | None
    providers: tuple[NormalizedProvider, ...] = ()
    check_ids: tuple[str, ...] = ()
    links: tuple[NormalizedReference, ...] = ()

    @model_validator(mode="after")
    def _validate_url(self) -> NormalizedService:
        if self.url is None:
            return self
        if self.kind is None:
            if safe_v1_endpoint(self.url) != self.url:
                raise PydanticCustomError("unsafe_normalized_url", "normalized URL is unsafe")
            return self
        try:
            validate_service_url(self.url, self.kind)
        except ValueError:
            raise PydanticCustomError("unsafe_normalized_url", "normalized URL is unsafe") from None
        return self


class NormalizedCheckDefinition(SafeModel):
    id: str
    service_id: str | None
    type: Literal["http"] = "http"
    target: str | None
    state: Literal["not_run"] = "not_run"

    @field_validator("target")
    @classmethod
    def _validate_target(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return validate_check_target(value)
        except ValueError:
            raise PydanticCustomError("unsafe_normalized_url", "normalized URL is unsafe") from None


class NormalizedTask(SafeModel):
    id: str
    description: str | None
    starts: tuple[str, ...] = ()
    stops: tuple[str, ...] = ()


class NormalizedAction(SafeModel):
    id: str
    type: ActionType
    label: str
    service_id: str | None = None
    url: str | None = None
    reference_rel: ReferenceRel | None = None
    task_id: str | None = None

    @model_validator(mode="after")
    def _validate_relationship(self) -> NormalizedAction:
        if self.type == "open_url":
            is_valid = (
                self.service_id is not None
                and self.url is not None
                and self.reference_rel is None
                and self.task_id is None
                and self.id == f"service:{self.service_id}:open"
            )
        elif self.type == "copy_endpoint":
            is_valid = (
                self.service_id is not None
                and self.url is not None
                and self.reference_rel is None
                and self.task_id is None
                and self.id == f"service:{self.service_id}:copy"
            )
        elif self.type == "open_reference":
            is_valid = (
                self.service_id is not None
                and self.url is not None
                and self.reference_rel is not None
                and self.task_id is None
                and self.id == f"service:{self.service_id}:reference:{self.reference_rel}"
            )
        elif self.type == "start_dev":
            is_valid = (
                self.service_id is None
                and self.url is None
                and self.reference_rel is None
                and self.task_id is None
                and self.id == "project:start_dev"
            )
        else:
            is_valid = (
                self.service_id is None
                and self.url is None
                and self.reference_rel is None
                and self.task_id is not None
                and self.id == f"task:{self.task_id}"
            )
        if not is_valid:
            raise PydanticCustomError("invalid_action_relationship", "action relationship is invalid")
        return self


def _derive_v2_actions(
    services: tuple[NormalizedService, ...],
    tasks: tuple[NormalizedTask, ...],
) -> tuple[NormalizedAction, ...]:
    """Derive the exact canonical action tuple from normalized v2 topology."""
    actions: list[NormalizedAction] = []
    for service in services:
        if service.display == "hidden":
            continue
        if service.kind == "web":
            actions.append(
                NormalizedAction(
                    id=f"service:{service.id}:open",
                    type="open_url",
                    label=f"Open {service.name}",
                    service_id=service.id,
                    url=service.url,
                )
            )
        elif service.kind in {"api", "protocol", "database"}:
            actions.append(
                NormalizedAction(
                    id=f"service:{service.id}:copy",
                    type="copy_endpoint",
                    label=f"Copy {service.name} endpoint",
                    service_id=service.id,
                    url=service.url,
                )
            )
        actions.extend(
            NormalizedAction(
                id=f"service:{service.id}:reference:{reference.rel}",
                type="open_reference",
                label=f"Open {service.name} {reference.rel}",
                service_id=service.id,
                url=reference.url,
                reference_rel=reference.rel,
            )
            for reference in service.links
        )
    if any(
        service.display != "hidden" and any(provider.type == "dev" for provider in service.providers)
        for service in services
    ):
        actions.append(NormalizedAction(id="project:start_dev", type="start_dev", label="Start development"))
    non_hidden_service_ids = {service.id for service in services if service.display != "hidden"}
    for task in tasks:
        if set(task.starts).union(task.stops).intersection(non_hidden_service_ids):
            actions.append(
                NormalizedAction(
                    id=f"task:{task.id}",
                    type="run_task",
                    label=f"Run task {task.id}",
                    task_id=task.id,
                )
            )
    return tuple(sorted(actions, key=lambda action: action.id))


_WARNING_CONTRACTS: dict[WarningCode, tuple[str, tuple[str, ...]]] = {
    "lifecycle_v1_metadata_incomplete": ("Lifecycle v1 metadata is incomplete.", ()),
    "unsafe_endpoint_omitted": ("Unsafe endpoint was omitted.", ("owner_type", "owner_id", "field")),
    "unsafe_path_omitted": ("Unsafe project path was omitted.", ("owner_type", "owner_id", "index", "field")),
    "duplicate_requirement_collapsed": (
        "Duplicate requirement was collapsed.",
        ("requirement_type", "first_index", "duplicate_index"),
    ),
}


def _is_nonnegative_index(value: WarningScalar) -> bool:
    return type(value) is int and value >= 0


def _warning_details_match_domain(code: WarningCode, details: Mapping[str, WarningScalar]) -> bool:
    if code == "lifecycle_v1_metadata_incomplete":
        return not details
    if code == "unsafe_endpoint_omitted":
        owner_type = details["owner_type"]
        owner_id = details["owner_id"]
        field = details["field"]
        return isinstance(owner_id, str) and (owner_type, field) in {("service", "url"), ("check", "target")}
    if code == "unsafe_path_omitted":
        owner_type = details["owner_type"]
        owner_id = details["owner_id"]
        index = details["index"]
        field = details["field"]
        if owner_type == "env_file":
            return owner_id is None and index is None and field == "env_file"
        if owner_type == "required_path":
            return owner_id is None and _is_nonnegative_index(index) and field == "path"
        if owner_type == "required_tool":
            return owner_id is None and _is_nonnegative_index(index) and field == "tool"
        if owner_type in {"process", "task"}:
            return isinstance(owner_id, str) and index is None and field == "cwd"
        return False
    first_index = details["first_index"]
    duplicate_index = details["duplicate_index"]
    if not isinstance(first_index, int) or not isinstance(duplicate_index, int):
        return False
    return (
        details["requirement_type"] in {"tool", "path"}
        and first_index >= 0
        and duplicate_index >= 0
        and first_index < duplicate_index
    )


class NormalizationWarning(SafeModel):
    code: WarningCode
    message: str
    details: Mapping[str, WarningScalar]

    @field_validator("details", mode="before")
    @classmethod
    def _validate_detail_scalar_types(cls, value: object) -> object:
        if isinstance(value, Mapping) and any(
            type(key) is not str or not (type(item) in {str, int} or item is None) for key, item in value.items()
        ):
            raise PydanticCustomError("invalid_warning_contract", "warning details are invalid")
        return value

    @field_serializer("details")
    def _serialize_details(self, value: Mapping[str, WarningScalar]) -> dict[str, WarningScalar]:
        return dict(value)

    @model_validator(mode="after")
    def _validate_contract(self) -> NormalizationWarning:
        message, keys = _WARNING_CONTRACTS[self.code]
        if (
            self.message != message
            or tuple(self.details) != keys
            or not _warning_details_match_domain(self.code, self.details)
        ):
            raise PydanticCustomError("invalid_warning_contract", "warning message or details are invalid")
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))
        return self

    def __deepcopy__(self, memo: dict[int, Any] | None = None) -> Self:
        memo = {} if memo is None else memo
        model_type = type(self)
        copied = model_type.__new__(model_type)
        memo[id(self)] = copied
        copied.__setstate__(deepcopy(self.__getstate__(), memo))
        return copied

    def __getstate__(self) -> dict[Any, Any]:
        state = super().__getstate__()
        state["__dict__"] = {**state["__dict__"], "details": dict(self.details)}
        return state

    def __setstate__(self, state: dict[Any, Any]) -> None:
        super().__setstate__(state)
        object.__setattr__(self, "details", MappingProxyType(dict(self.details)))


class SafeProjectPath(SafeModel):
    path: str

    @field_validator("path")
    @classmethod
    def _validate_path(cls, value: str) -> str:
        try:
            return validate_project_relative_path(value, allow_dot=True)
        except ValueError:
            raise PydanticCustomError("unsafe_normalized_path", "normalized path is unsafe") from None


class SafeExecutableName(SafeModel):
    name: str

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        try:
            return validate_bare_executable(value)
        except ValueError:
            raise PydanticCustomError("unsafe_normalized_tool", "normalized tool is unsafe") from None


class PathDiagnosticSource(SafeModel):
    id: str
    owner_id: str | None = None
    source_index: int | None = None
    path: SafeProjectPath | None = None


class ToolDiagnosticSource(SafeModel):
    id: str
    source_index: int | None = None
    tool: SafeExecutableName | None = None


class EnvironmentDiagnosticSource(SafeModel):
    id: str
    name: str
    aliases: tuple[str, ...] = ()
    required: bool = False
    has_usable_default: bool = False


class HttpDiagnosticSource(SafeModel):
    id: str
    service_id: str | None
    target: str | None
    timeout: float
    attempts: int

    @field_validator("target")
    @classmethod
    def _validate_target(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return validate_check_target(value)
        except ValueError:
            raise PydanticCustomError("unsafe_normalized_url", "normalized URL is unsafe") from None

    @model_validator(mode="after")
    def _validate_id(self) -> HttpDiagnosticSource:
        prefix = "service-check:"
        suffix = self.id[len(prefix) :] if self.id.startswith(prefix) else None
        if suffix is None or (not suffix and self.service_id is not None):
            raise PydanticCustomError("invalid_http_diagnostic_id", "HTTP diagnostic ID is invalid")
        return self


class DiagnosticInputs(SafeModel):
    env_file: PathDiagnosticSource | None = None
    tools: tuple[ToolDiagnosticSource, ...] = ()
    required_paths: tuple[PathDiagnosticSource, ...] = ()
    process_cwds: tuple[PathDiagnosticSource, ...] = ()
    unsafe_task_cwd_ids: tuple[str, ...] = ()
    environment: tuple[EnvironmentDiagnosticSource, ...] = ()
    http_checks: tuple[HttpDiagnosticSource, ...] = ()


def _is_unique_sorted(values: tuple[str, ...]) -> bool:
    return values == tuple(sorted(values)) and len(values) == len(set(values))


def _warning_sort_key(warning: NormalizationWarning) -> tuple[str, str, str]:
    return (
        warning.code,
        warning.message,
        json.dumps(dict(warning.details), ensure_ascii=False, separators=(",", ":")),
    )


def _valid_source_index(value: int | None) -> bool:
    return value is not None and value >= 0


def _diagnostic_sources_are_canonical(inputs: DiagnosticInputs) -> bool:  # noqa: C901
    groups = (
        inputs.tools,
        inputs.required_paths,
        inputs.process_cwds,
        inputs.environment,
        inputs.http_checks,
    )
    for sources in groups:
        ids = tuple(source.id for source in sources)
        if not _is_unique_sorted(ids):
            return False
    all_ids = [source.id for sources in groups for source in sources]
    if inputs.env_file is not None:
        all_ids.append(inputs.env_file.id)
    if len(all_ids) != len(set(all_ids)):
        return False

    env_file = inputs.env_file
    if env_file is not None:
        if env_file.owner_id is not None or env_file.source_index is not None:
            return False
        if env_file.path is None:
            if env_file.id != "unsafe-path:env-file":
                return False
        elif env_file.path.path == "." or env_file.id != f"env-file:{env_file.path.path}":
            return False

    for source in inputs.tools:
        if source.tool is None:
            if not _valid_source_index(source.source_index) or source.id != (
                f"unsafe-path:required-tool:{source.source_index}"
            ):
                return False
        elif source.source_index is not None or source.id != f"tool:{source.tool.name}":
            return False

    for source in inputs.required_paths:
        if source.owner_id is not None:
            return False
        if source.path is None:
            if not _valid_source_index(source.source_index) or source.id != (
                f"unsafe-path:required:{source.source_index}"
            ):
                return False
        elif source.source_index is not None or source.path.path == "." or source.id != f"path:{source.path.path}":
            return False

    process_owner_ids: list[str] = []
    for source in inputs.process_cwds:
        if source.owner_id is None:
            return False
        process_owner_ids.append(source.owner_id)
        if source.path is None:
            if not _valid_source_index(source.source_index) or source.id != (
                f"unsafe-path:process-cwd:{source.source_index}"
            ):
                return False
        elif source.source_index is not None or source.id != f"process-cwd:{source.owner_id}":
            return False
    if len(process_owner_ids) != len(set(process_owner_ids)):
        return False

    if not _is_unique_sorted(inputs.unsafe_task_cwd_ids):
        return False

    for source in inputs.environment:
        if source.id != f"env:{source.name}" or source.aliases != tuple(sorted(source.aliases)):
            return False
    return True


def _common_postconditions_hold(project: NormalizedLifecycleProject) -> bool:
    identity_groups = (
        tuple(item.name for item in project.environment),
        tuple(item.id for item in project.services),
        tuple(item.id for item in project.checks),
        tuple(item.id for item in project.tasks),
        tuple(item.id for item in project.actions),
    )
    if any(not _is_unique_sorted(identities) for identities in identity_groups):
        return False
    if any(item.aliases != tuple(sorted(item.aliases)) for item in project.environment):
        return False
    for service in project.services:
        provider_keys = tuple((provider.type, provider.id) for provider in service.providers)
        if provider_keys != tuple(sorted(provider_keys)) or len(provider_keys) != len(set(provider_keys)):
            return False
        link_keys = tuple((link.rel, link.url) for link in service.links)
        if link_keys != tuple(sorted(link_keys)) or len({link.rel for link in service.links}) != len(service.links):
            return False
        if not _is_unique_sorted(service.check_ids):
            return False
    for task in project.tasks:
        if not _is_unique_sorted(task.starts) or not _is_unique_sorted(task.stops):
            return False
    warning_keys = tuple(_warning_sort_key(warning) for warning in project.warnings)
    if warning_keys != tuple(sorted(warning_keys)):
        return False
    return bool(project.diagnostic_inputs.process_cwds) and _diagnostic_sources_are_canonical(project.diagnostic_inputs)


def _environment_diagnostics_match(project: NormalizedLifecycleProject) -> bool:
    diagnostics = project.diagnostic_inputs.environment
    if tuple(source.name for source in diagnostics) != tuple(item.name for item in project.environment):
        return False
    return all(
        source.aliases == item.aliases and source.required == item.required
        for source, item in zip(diagnostics, project.environment, strict=True)
    )


def _http_diagnostics_mirror_checks(project: NormalizedLifecycleProject) -> bool:
    sources = project.diagnostic_inputs.http_checks
    if len(sources) != len(project.checks):
        return False
    return all(
        source.id == f"service-check:{check.id}"
        and source.service_id == check.service_id
        and source.target == check.target
        for source, check in zip(sources, project.checks, strict=True)
    )


def _task_warning_provenance_matches_tasks(project: NormalizedLifecycleProject) -> bool:
    task_ids = {task.id for task in project.tasks}
    return set(project.diagnostic_inputs.unsafe_task_cwd_ids).issubset(task_ids)


def _v1_process_source_indices_are_canonical(project: NormalizedLifecycleProject) -> bool:
    sources = project.diagnostic_inputs.process_cwds
    owner_ids = [source.owner_id for source in sources]
    if any(owner_id is None for owner_id in owner_ids):
        return False
    owner_positions = {
        owner_id: index
        for index, owner_id in enumerate(sorted(owner_id for owner_id in owner_ids if owner_id is not None))
    }
    return all(
        source.path is not None or source.source_index == owner_positions[source.owner_id]
        for source in sources
        if source.owner_id is not None
    )


def _v1_omission_warnings_match(project: NormalizedLifecycleProject) -> bool:
    endpoint_warnings = {
        (warning.details["owner_type"], warning.details["owner_id"], warning.details["field"])
        for warning in project.warnings
        if warning.code == "unsafe_endpoint_omitted"
    }
    expected_endpoint_warnings = {
        *[("service", service.id, "url") for service in project.services if service.url is None],
        *[("check", check.id, "target") for check in project.checks if check.target is None],
    }
    if endpoint_warnings != expected_endpoint_warnings:
        return False

    diagnostic_path_warnings = {
        (
            warning.details["owner_type"],
            warning.details["owner_id"],
            warning.details["index"],
            warning.details["field"],
        )
        for warning in project.warnings
        if warning.code == "unsafe_path_omitted" and warning.details["owner_type"] != "task"
    }
    expected_path_warnings: set[tuple[WarningScalar, WarningScalar, WarningScalar, WarningScalar]] = set()
    inputs = project.diagnostic_inputs
    if inputs.env_file is not None and inputs.env_file.path is None:
        expected_path_warnings.add(("env_file", None, None, "env_file"))
    for source in inputs.required_paths:
        if source.path is None:
            expected_path_warnings.add(("required_path", None, source.source_index, "path"))
    for source in inputs.tools:
        if source.tool is None:
            expected_path_warnings.add(("required_tool", None, source.source_index, "tool"))
    for source in inputs.process_cwds:
        if source.path is None:
            expected_path_warnings.add(("process", source.owner_id, None, "cwd"))
    if diagnostic_path_warnings != expected_path_warnings:
        return False

    task_warnings = {
        warning.details["owner_id"]
        for warning in project.warnings
        if warning.code == "unsafe_path_omitted" and warning.details["owner_type"] == "task"
    }
    expected_task_warnings = set(inputs.unsafe_task_cwd_ids)
    return task_warnings == expected_task_warnings


def _v1_postconditions_hold(project: NormalizedLifecycleProject) -> bool:
    if (
        project.metadata_complete
        or not project.project.name
        or project.project.description is not None
        or project.project.guide is not None
        or project.actions
    ):
        return False
    if any(
        service.name is not None
        or service.description is not None
        or service.kind is not None
        or service.display is not None
        or service.primary is not None
        or service.tech is not None
        or service.providers
        or service.check_ids
        or service.links
        for service in project.services
    ):
        return False
    if any(check.service_id is not None for check in project.checks):
        return False
    if any(task.starts or task.stops for task in project.tasks):
        return False
    if sum(warning.code == "lifecycle_v1_metadata_incomplete" for warning in project.warnings) != 1:
        return False
    return (
        _environment_diagnostics_match(project)
        and _http_diagnostics_mirror_checks(project)
        and _task_warning_provenance_matches_tasks(project)
        and _v1_process_source_indices_are_canonical(project)
        and _v1_omission_warnings_match(project)
    )


def _has_valid_identifier(value: str) -> bool:
    try:
        validate_identifier(value)
    except ValueError:
        return False
    return True


def _v2_postconditions_hold(project: NormalizedLifecycleProject) -> bool:  # noqa: C901
    if (
        not project.metadata_complete
        or project.warnings
        or project.project.template is None
        or not project.project.template.strip()
        or not project.project.name.strip()
    ):
        return False
    if any(not _has_valid_identifier(item.name) for item in project.environment) or any(
        not _has_valid_identifier(item.id) for item in (*project.services, *project.checks, *project.tasks)
    ):
        return False

    primary_services = [service for service in project.services if service.primary]
    if (project.services and len(primary_services) != 1) or (not project.services and primary_services):
        return False
    if primary_services and primary_services[0].display == "hidden":
        return False
    for service in project.services:
        if (
            service.name is None
            or not service.name.strip()
            or service.description is None
            or not service.description.strip()
            or service.url is None
            or service.kind is None
            or service.display is None
            or service.primary is None
        ):
            return False

    service_ids = {service.id for service in project.services}
    checks_by_service: dict[str, list[str]] = {service.id: [] for service in project.services}
    for check in project.checks:
        if check.service_id is None or check.service_id not in service_ids or check.target is None:
            return False
        checks_by_service[check.service_id].append(check.id)
    if any(service.check_ids != tuple(sorted(checks_by_service[service.id])) for service in project.services):
        return False

    tasks_by_id = {task.id: task for task in project.tasks}
    expected_task_providers: dict[str, set[str]] = {service.id: set() for service in project.services}
    for task in project.tasks:
        if any(service_id not in service_ids for service_id in (*task.starts, *task.stops)):
            return False
        for service_id in task.starts:
            expected_task_providers[service_id].add(task.id)

    process_owner_ids = {
        source.owner_id for source in project.diagnostic_inputs.process_cwds if source.owner_id is not None
    }
    if any(not _has_valid_identifier(owner_id) for owner_id in process_owner_ids):
        return False
    actual_task_providers: dict[str, set[str]] = {service.id: set() for service in project.services}
    for service in project.services:
        for provider in service.providers:
            if provider.type == "dev":
                if provider.process_id is None or provider.process_id not in process_owner_ids:
                    return False
                if not _has_valid_identifier(provider.process_id):
                    return False
            else:
                if provider.task_id is None or provider.task_id not in tasks_by_id:
                    return False
                actual_task_providers[service.id].add(provider.task_id)
    if actual_task_providers != expected_task_providers:
        return False

    inputs = project.diagnostic_inputs
    if (
        (inputs.env_file is not None and inputs.env_file.path is None)
        or any(source.tool is None or source.source_index is not None for source in inputs.tools)
        or any(source.path is None or source.source_index is not None for source in inputs.required_paths)
        or any(
            source.path is None or source.source_index is not None or source.owner_id is None
            for source in inputs.process_cwds
        )
        or bool(inputs.unsafe_task_cwd_ids)
        or any(not _has_valid_identifier(source.name) for source in inputs.environment)
        or any(source.attempts <= 0 for source in inputs.http_checks)
    ):
        return False
    if (
        not _environment_diagnostics_match(project)
        or not _http_diagnostics_mirror_checks(project)
        or not _task_warning_provenance_matches_tasks(project)
    ):
        return False
    return project.actions == _derive_v2_actions(project.services, project.tasks)


class NormalizedLifecycleProject(SafeModel):
    lifecycle_version: Literal[1, 2]
    project: NormalizedProject
    metadata_complete: bool
    environment: tuple[NormalizedEnvironmentRequirement, ...] = ()
    services: tuple[NormalizedService, ...] = ()
    checks: tuple[NormalizedCheckDefinition, ...] = ()
    tasks: tuple[NormalizedTask, ...] = ()
    actions: tuple[NormalizedAction, ...] = ()
    warnings: tuple[NormalizationWarning, ...] = ()
    diagnostic_inputs: DiagnosticInputs = Field(default_factory=DiagnosticInputs)

    @model_validator(mode="after")
    def _validate_postconditions(self) -> NormalizedLifecycleProject:
        if not _common_postconditions_hold(self):
            raise PydanticCustomError("invalid_normalized_project", "normalized project is invalid")
        profile_is_valid = (
            _v1_postconditions_hold(self) if self.lifecycle_version == 1 else _v2_postconditions_hold(self)
        )
        if not profile_is_valid:
            raise PydanticCustomError("invalid_normalized_project", "normalized project is invalid")
        return self
