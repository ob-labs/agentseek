"""Versioned lifecycle JSON data-transfer objects and serialization."""

from __future__ import annotations

import json
from typing import Literal, cast

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic_core import PydanticCustomError

from agentseek.cli.lifecycle.discovery import (
    NormalizationWarning,
    NormalizedAction,
    NormalizedCheckDefinition,
    NormalizedEnvironmentRequirement,
    NormalizedLifecycleProject,
    NormalizedProject,
    NormalizedProjectFile,
    NormalizedProvider,
    NormalizedReference,
    NormalizedService,
    NormalizedTask,
)


class JsonDTO(BaseModel):
    """Immutable, closed model base for the public JSON wire contract."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ProjectFileDTO(JsonDTO):
    path: str
    rel: Literal["guide"]

    @classmethod
    def from_normalized(cls, project_file: NormalizedProjectFile) -> ProjectFileDTO:
        return cls(path=project_file.path, rel=project_file.rel)


class ProjectDTO(JsonDTO):
    template: str | None
    name: str
    description: str | None
    guide: ProjectFileDTO | None

    @classmethod
    def from_normalized(cls, project: NormalizedProject) -> ProjectDTO:
        return cls(
            template=project.template,
            name=project.name,
            description=project.description,
            guide=ProjectFileDTO.from_normalized(project.guide) if project.guide is not None else None,
        )


class EnvironmentRequirementDTO(JsonDTO):
    name: str
    required: bool
    description: str | None
    aliases: tuple[str, ...]

    @classmethod
    def from_normalized(
        cls,
        requirement: NormalizedEnvironmentRequirement,
    ) -> EnvironmentRequirementDTO:
        return cls(
            name=requirement.name,
            required=requirement.required,
            description=requirement.description,
            aliases=requirement.aliases,
        )


class ProviderDTO(JsonDTO):
    type: Literal["dev", "task"]
    id: str
    process_id: str | None
    task_id: str | None

    @classmethod
    def from_normalized(cls, provider: NormalizedProvider) -> ProviderDTO:
        return cls(
            type=provider.type,
            id=provider.id,
            process_id=provider.process_id,
            task_id=provider.task_id,
        )


class ReferenceDTO(JsonDTO):
    rel: Literal["docs", "api_docs", "studio"]
    url: str

    @classmethod
    def from_normalized(cls, reference: NormalizedReference) -> ReferenceDTO:
        return cls(rel=reference.rel, url=reference.url)


class ServiceDTO(JsonDTO):
    id: str
    name: str | None
    description: str | None
    url: str | None
    kind: Literal["web", "api", "protocol", "database", "other"] | None
    display: Literal["default", "advanced", "hidden"] | None
    primary: bool | None
    tech: str | None
    providers: tuple[ProviderDTO, ...]
    check_ids: tuple[str, ...]
    links: tuple[ReferenceDTO, ...]

    @classmethod
    def from_normalized(cls, service: NormalizedService) -> ServiceDTO:
        return cls(
            id=service.id,
            name=service.name,
            description=service.description,
            url=service.url,
            kind=service.kind,
            display=service.display,
            primary=service.primary,
            tech=service.tech,
            providers=tuple(ProviderDTO.from_normalized(provider) for provider in service.providers),
            check_ids=service.check_ids,
            links=tuple(ReferenceDTO.from_normalized(reference) for reference in service.links),
        )


class CheckDefinitionDTO(JsonDTO):
    id: str
    service_id: str | None
    type: Literal["http"]
    target: str | None
    state: Literal["not_run"]

    @classmethod
    def from_normalized(cls, check: NormalizedCheckDefinition) -> CheckDefinitionDTO:
        return cls(
            id=check.id,
            service_id=check.service_id,
            type=check.type,
            target=check.target,
            state=check.state,
        )


class TaskDTO(JsonDTO):
    id: str
    description: str | None
    starts: tuple[str, ...]
    stops: tuple[str, ...]

    @classmethod
    def from_normalized(cls, task: NormalizedTask) -> TaskDTO:
        return cls(
            id=task.id,
            description=task.description,
            starts=task.starts,
            stops=task.stops,
        )


class ActionDTO(JsonDTO):
    id: str
    type: Literal["open_url", "copy_endpoint", "open_reference", "start_dev", "run_task"]
    label: str
    service_id: str | None
    url: str | None
    reference_rel: Literal["docs", "api_docs", "studio"] | None
    task_id: str | None

    @classmethod
    def from_normalized(cls, action: NormalizedAction) -> ActionDTO:
        return cls(
            id=action.id,
            type=action.type,
            label=action.label,
            service_id=action.service_id,
            url=action.url,
            reference_rel=action.reference_rel,
            task_id=action.task_id,
        )


class EmptyWarningDetailsDTO(JsonDTO):
    pass


class UnsafeEndpointWarningDetailsDTO(JsonDTO):
    owner_type: Literal["service", "check"]
    owner_id: str
    field: Literal["url", "target"]


class UnsafePathWarningDetailsDTO(JsonDTO):
    owner_type: Literal["env_file", "required_path", "required_tool", "process", "task"]
    owner_id: str | None
    index: int | None
    field: Literal["env_file", "path", "tool", "cwd"]


class DuplicateRequirementWarningDetailsDTO(JsonDTO):
    requirement_type: Literal["tool", "path"]
    first_index: int
    duplicate_index: int


WarningCode = Literal[
    "lifecycle_v1_metadata_incomplete",
    "unsafe_endpoint_omitted",
    "unsafe_path_omitted",
    "duplicate_requirement_collapsed",
]
WarningDetailsDTO = (
    EmptyWarningDetailsDTO
    | UnsafeEndpointWarningDetailsDTO
    | UnsafePathWarningDetailsDTO
    | DuplicateRequirementWarningDetailsDTO
)
_WARNING_DTO_CONTRACTS: dict[WarningCode, tuple[str, type[JsonDTO]]] = {
    "lifecycle_v1_metadata_incomplete": (
        "Lifecycle v1 metadata is incomplete.",
        EmptyWarningDetailsDTO,
    ),
    "unsafe_endpoint_omitted": (
        "Unsafe endpoint was omitted.",
        UnsafeEndpointWarningDetailsDTO,
    ),
    "unsafe_path_omitted": (
        "Unsafe project path was omitted.",
        UnsafePathWarningDetailsDTO,
    ),
    "duplicate_requirement_collapsed": (
        "Duplicate requirement was collapsed.",
        DuplicateRequirementWarningDetailsDTO,
    ),
}


class WarningDTO(JsonDTO):
    code: WarningCode
    message: str
    details: WarningDetailsDTO

    @classmethod
    def from_normalized(cls, warning: NormalizationWarning) -> WarningDTO:
        details = warning.details
        if warning.code == "lifecycle_v1_metadata_incomplete":
            projected_details: WarningDetailsDTO = EmptyWarningDetailsDTO()
        elif warning.code == "unsafe_endpoint_omitted":
            projected_details = UnsafeEndpointWarningDetailsDTO(
                owner_type=cast("Literal['service', 'check']", details["owner_type"]),
                owner_id=cast("str", details["owner_id"]),
                field=cast("Literal['url', 'target']", details["field"]),
            )
        elif warning.code == "unsafe_path_omitted":
            projected_details = UnsafePathWarningDetailsDTO(
                owner_type=cast(
                    "Literal['env_file', 'required_path', 'required_tool', 'process', 'task']",
                    details["owner_type"],
                ),
                owner_id=cast("str | None", details["owner_id"]),
                index=cast("int | None", details["index"]),
                field=cast("Literal['env_file', 'path', 'tool', 'cwd']", details["field"]),
            )
        else:
            projected_details = DuplicateRequirementWarningDetailsDTO(
                requirement_type=cast("Literal['tool', 'path']", details["requirement_type"]),
                first_index=cast("int", details["first_index"]),
                duplicate_index=cast("int", details["duplicate_index"]),
            )
        return cls(code=warning.code, message=warning.message, details=projected_details)

    @model_validator(mode="after")
    def _validate_contract(self) -> WarningDTO:
        message, details_type = _WARNING_DTO_CONTRACTS[self.code]
        if self.message != message or not isinstance(self.details, details_type):
            raise PydanticCustomError(
                "invalid_warning_contract",
                "warning message or details are invalid",
            )
        return self


class InfoDataDTO(JsonDTO):
    project: ProjectDTO
    metadata_complete: bool
    environment: tuple[EnvironmentRequirementDTO, ...]
    services: tuple[ServiceDTO, ...]
    checks: tuple[CheckDefinitionDTO, ...]
    tasks: tuple[TaskDTO, ...]
    actions: tuple[ActionDTO, ...]
    warnings: tuple[WarningDTO, ...]

    @classmethod
    def from_normalized(cls, project: NormalizedLifecycleProject) -> InfoDataDTO:
        """Project only the fields in the public info contract."""
        return cls(
            project=ProjectDTO.from_normalized(project.project),
            metadata_complete=project.metadata_complete,
            environment=tuple(
                EnvironmentRequirementDTO.from_normalized(requirement) for requirement in project.environment
            ),
            services=tuple(ServiceDTO.from_normalized(service) for service in project.services),
            checks=tuple(CheckDefinitionDTO.from_normalized(check) for check in project.checks),
            tasks=tuple(TaskDTO.from_normalized(task) for task in project.tasks),
            actions=tuple(ActionDTO.from_normalized(action) for action in project.actions),
            warnings=tuple(WarningDTO.from_normalized(warning) for warning in project.warnings),
        )


class InfoSuccessEnvelopeDTO(JsonDTO):
    schema_version: Literal[1] = 1
    command: Literal["info"] = "info"
    ok: Literal[True] = True
    lifecycle_version: Literal[1, 2]
    data: InfoDataDTO
    error: None = None


class EmptyErrorDetailsDTO(JsonDTO):
    pass


class CliOptionConflictDetailsDTO(JsonDTO):
    options: tuple[Literal["--json"], Literal["--strict"]]


class TomlErrorDetailsDTO(JsonDTO):
    line: int | None
    column: int | None


class ValidationIssueDTO(JsonDTO):
    path: str
    code: str
    message: str


class ValidationErrorDetailsDTO(JsonDTO):
    issues: tuple[ValidationIssueDTO, ...]


class UnsupportedVersionDetailsDTO(JsonDTO):
    found: int | None
    supported: tuple[Literal[1], Literal[2]]


ErrorCode = Literal[
    "cli_option_conflict",
    "lifecycle_not_found",
    "lifecycle_toml_invalid",
    "lifecycle_validation_failed",
    "lifecycle_version_unsupported",
    "internal_error",
]
ErrorDetailsDTO = (
    EmptyErrorDetailsDTO
    | CliOptionConflictDetailsDTO
    | TomlErrorDetailsDTO
    | ValidationErrorDetailsDTO
    | UnsupportedVersionDetailsDTO
)
_ERROR_CONTRACTS: dict[ErrorCode, tuple[str, type[JsonDTO]]] = {
    "cli_option_conflict": (
        "Options --strict and --json cannot be combined.",
        CliOptionConflictDetailsDTO,
    ),
    "lifecycle_not_found": ("No lifecycle.toml was found.", EmptyErrorDetailsDTO),
    "lifecycle_toml_invalid": ("The lifecycle TOML is invalid.", TomlErrorDetailsDTO),
    "lifecycle_validation_failed": (
        "The lifecycle specification is invalid.",
        ValidationErrorDetailsDTO,
    ),
    "lifecycle_version_unsupported": (
        "The lifecycle version is unsupported.",
        UnsupportedVersionDetailsDTO,
    ),
    "internal_error": ("Unexpected internal error.", EmptyErrorDetailsDTO),
}


class ErrorDTO(JsonDTO):
    code: ErrorCode
    message: str
    details: ErrorDetailsDTO

    @model_validator(mode="after")
    def _validate_contract(self) -> ErrorDTO:
        message, details_type = _ERROR_CONTRACTS[self.code]
        if self.message != message or not isinstance(self.details, details_type):
            raise PydanticCustomError("invalid_error_contract", "error message or details are invalid")
        return self


class InfoErrorEnvelopeDTO(JsonDTO):
    schema_version: Literal[1] = 1
    command: Literal["info"] = "info"
    ok: Literal[False] = False
    lifecycle_version: int | None
    data: None = None
    error: ErrorDTO


class CheckResultDTO(JsonDTO):
    id: str
    scope: Literal["project", "service"]
    service_id: str | None
    type: Literal["lifecycle", "tool", "path", "env_file", "env", "process_cwd", "http"]
    state: Literal["not_run", "pass", "fail"]
    message: str
    target: str | None

    @model_validator(mode="after")
    def _validate_scope(self) -> CheckResultDTO:
        if (self.scope == "project" and self.service_id is not None) or (
            self.scope == "service" and self.service_id is None
        ):
            raise PydanticCustomError("invalid_check_result_scope", "check result scope is invalid")
        return self


class DoctorDataDTO(JsonDTO):
    passed: bool
    live_requested: bool
    results: tuple[CheckResultDTO, ...]
    warnings: tuple[WarningDTO, ...]

    @model_validator(mode="after")
    def _validate_results(self) -> DoctorDataDTO:
        result_ids = tuple(result.id for result in self.results)
        expected_passed = not any(result.state == "fail" for result in self.results)
        if (
            result_ids != tuple(sorted(result_ids))
            or len(result_ids) != len(set(result_ids))
            or self.passed != expected_passed
        ):
            raise PydanticCustomError("invalid_doctor_results", "doctor results are invalid")
        return self


class DoctorSuccessEnvelopeDTO(JsonDTO):
    schema_version: Literal[1] = 1
    command: Literal["doctor"] = "doctor"
    ok: Literal[True] = True
    lifecycle_version: Literal[1, 2]
    data: DoctorDataDTO
    error: None = None


class DoctorErrorEnvelopeDTO(JsonDTO):
    schema_version: Literal[1] = 1
    command: Literal["doctor"] = "doctor"
    ok: Literal[False] = False
    lifecycle_version: int | None
    data: None = None
    error: ErrorDTO


def serialize_json(dto: JsonDTO) -> str:
    """Serialize one DTO with the normative compact JSON representation."""
    return (
        json.dumps(
            dto.model_dump(mode="json"),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        + "\n"
    )


__all__ = [
    "ActionDTO",
    "CheckDefinitionDTO",
    "CheckResultDTO",
    "CliOptionConflictDetailsDTO",
    "DoctorDataDTO",
    "DoctorErrorEnvelopeDTO",
    "DoctorSuccessEnvelopeDTO",
    "DuplicateRequirementWarningDetailsDTO",
    "EmptyErrorDetailsDTO",
    "EmptyWarningDetailsDTO",
    "EnvironmentRequirementDTO",
    "ErrorDTO",
    "InfoDataDTO",
    "InfoErrorEnvelopeDTO",
    "InfoSuccessEnvelopeDTO",
    "JsonDTO",
    "ProjectDTO",
    "ProjectFileDTO",
    "ProviderDTO",
    "ReferenceDTO",
    "ServiceDTO",
    "TaskDTO",
    "TomlErrorDetailsDTO",
    "UnsafeEndpointWarningDetailsDTO",
    "UnsafePathWarningDetailsDTO",
    "UnsupportedVersionDetailsDTO",
    "ValidationErrorDetailsDTO",
    "ValidationIssueDTO",
    "WarningDTO",
    "serialize_json",
]
