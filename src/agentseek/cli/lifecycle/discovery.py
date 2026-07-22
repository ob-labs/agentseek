"""Frozen normalized lifecycle discovery models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import PydanticCustomError

from agentseek.cli.lifecycle.safety import ReferenceRel, ServiceKind

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


class NormalizedCheckDefinition(SafeModel):
    id: str
    service_id: str | None
    type: Literal["http"] = "http"
    target: str | None
    state: Literal["not_run"] = "not_run"


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


_WARNING_CONTRACTS: dict[WarningCode, tuple[str, tuple[str, ...]]] = {
    "lifecycle_v1_metadata_incomplete": ("Lifecycle v1 metadata is incomplete.", ()),
    "unsafe_endpoint_omitted": ("Unsafe endpoint was omitted.", ("owner_type", "owner_id", "field")),
    "unsafe_path_omitted": ("Unsafe project path was omitted.", ("owner_type", "owner_id", "index", "field")),
    "duplicate_requirement_collapsed": (
        "Duplicate requirement was collapsed.",
        ("requirement_type", "first_index", "duplicate_index"),
    ),
}


class NormalizationWarning(SafeModel):
    code: WarningCode
    message: str
    details: dict[str, WarningScalar]

    @model_validator(mode="after")
    def _validate_contract(self) -> NormalizationWarning:
        message, keys = _WARNING_CONTRACTS[self.code]
        if self.message != message or tuple(self.details) != keys:
            raise PydanticCustomError("invalid_warning_contract", "warning message or details are invalid")
        object.__setattr__(self, "details", dict(self.details))
        return self


class SafeProjectPath(SafeModel):
    path: str


class SafeExecutableName(SafeModel):
    name: str


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

    @model_validator(mode="after")
    def _validate_id(self) -> HttpDiagnosticSource:
        prefix = "service-check:"
        if not self.id.startswith(prefix) or not self.id[len(prefix) :]:
            raise PydanticCustomError("invalid_http_diagnostic_id", "HTTP diagnostic ID is invalid")
        return self


class DiagnosticInputs(SafeModel):
    env_file: PathDiagnosticSource | None = None
    tools: tuple[ToolDiagnosticSource, ...] = ()
    required_paths: tuple[PathDiagnosticSource, ...] = ()
    process_cwds: tuple[PathDiagnosticSource, ...] = ()
    environment: tuple[EnvironmentDiagnosticSource, ...] = ()
    http_checks: tuple[HttpDiagnosticSource, ...] = ()


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
