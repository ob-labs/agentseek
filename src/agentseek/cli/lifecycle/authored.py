"""Authored lifecycle v1 and v2 models."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)
from pydantic_core import InitErrorDetails, PydanticCustomError

from agentseek.cli.lifecycle.safety import (
    UnsafeProjectPathError,
    resolve_confined_project_path,
    validate_bare_executable,
    validate_check_target,
    validate_identifier,
    validate_reference_url,
    validate_service_url,
)

SUPPORTED_LIFECYCLE_VERSIONS = (1, 2)
SUPPORTED_LIFECYCLE_VERSION = 2
_V1_LIFECYCLE_VERSION = 1
_PLACEHOLDER_PATTERN = re.compile(r"\$\{|\{\{")


class SpecModel(BaseModel):
    """Base model for lifecycle spec sections."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class RequiredList(SpecModel):
    required: tuple[str, ...] = ()


class EnvRequirement(SpecModel):
    required: bool = False
    default: str | None = None
    description: str = ""
    aliases: tuple[str, ...] = ()

    def keys(self, name: str) -> tuple[str, ...]:
        return (name, *self.aliases)


class ServiceV1(SpecModel):
    url: str


class ProcessV1(SpecModel):
    command: tuple[str, ...]
    cwd: str = "."

    @field_validator("command")
    @classmethod
    def _command_must_not_be_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise PydanticCustomError("empty_command", "command must not be empty")
        return value


class CheckV1(SpecModel):
    type: Literal["http"] = "http"
    target: str
    timeout: float = 2.0
    attempts: int = 1


class TaskV1(SpecModel):
    command: tuple[str, ...]
    cwd: str = "."
    description: str = ""

    @field_validator("command")
    @classmethod
    def _command_must_not_be_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise PydanticCustomError("empty_command", "command must not be empty")
        return value


class LifecycleSpecV1(SpecModel):
    path: Path
    version: int
    template: str = ""
    name: str = ""
    env_file: str | None = None
    tools: RequiredList = Field(default_factory=RequiredList)
    paths: RequiredList = Field(default_factory=RequiredList)
    env: dict[str, EnvRequirement] = Field(default_factory=dict)
    services: dict[str, ServiceV1] = Field(default_factory=dict)
    processes: dict[str, ProcessV1] = Field(default_factory=dict)
    checks: dict[str, CheckV1] = Field(default_factory=dict)
    tasks: dict[str, TaskV1] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_contract(self) -> LifecycleSpecV1:
        if self.version != _V1_LIFECYCLE_VERSION:
            raise PydanticCustomError("unsupported_version", "unsupported version {version}", {"version": self.version})
        if not self.name:
            raise PydanticCustomError("missing_name", "name must be set")
        if not self.processes:
            raise PydanticCustomError("missing_processes", "at least one process must be declared")
        return self

    @property
    def required_tools(self) -> tuple[str, ...]:
        return self.tools.required

    @property
    def required_paths(self) -> tuple[str, ...]:
        return self.paths.required


def _identifier(value: str) -> str:
    try:
        return validate_identifier(value)
    except ValueError:
        raise PydanticCustomError("invalid_identifier", "identifier is invalid") from None


Identifier = Annotated[str, AfterValidator(_identifier)]


def _blank(value: str) -> str:
    if not value.strip():
        raise PydanticCustomError("blank_value", "value must not be blank")
    return value


def _project_path(value: str, info: ValidationInfo, *, allow_dot: bool = False) -> str:
    project_root = (info.context or {}).get("project_root")
    if not isinstance(project_root, Path):
        raise PydanticCustomError("unsafe_project_path", "project path is unsafe")
    try:
        resolve_confined_project_path(project_root, value, allow_dot=allow_dot)
    except UnsafeProjectPathError:
        raise PydanticCustomError("unsafe_project_path", "project path is unsafe") from None
    return value


def _url_error(value: str, *, allowed_schemes: frozenset[str], reference: bool = False) -> PydanticCustomError:
    if _PLACEHOLDER_PATTERN.search(value):
        return PydanticCustomError("unresolved_placeholder", "url contains unresolved placeholder")
    if any(ord(char) <= 0x1F or ord(char) == 0x7F for char in value):
        return PydanticCustomError("url_control_forbidden", "url contains control characters")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return PydanticCustomError(
            "reference_host_invalid" if reference else "url_host_required", "url host is invalid"
        )
    if not parsed.scheme:
        return PydanticCustomError("url_absolute_required", "url must be absolute")
    if parsed.scheme not in allowed_schemes:
        return PydanticCustomError("url_scheme_invalid", "url scheme is invalid")
    if not hostname or parsed.netloc.rsplit("@", 1)[-1].endswith(":") or (port is not None and not 0 <= port <= 65535):
        return PydanticCustomError(
            "reference_host_invalid" if reference else "url_host_required", "url host is invalid"
        )
    if parsed.username is not None or parsed.password is not None:
        return PydanticCustomError("url_userinfo_forbidden", "url userinfo is forbidden")
    if "?" in value:
        return PydanticCustomError("url_query_forbidden", "url query is forbidden")
    return PydanticCustomError("url_fragment_forbidden", "url fragment is forbidden")


def _validate_service_endpoint(value: str, kind: str) -> str:
    try:
        return validate_service_url(value, kind)  # type: ignore[arg-type]
    except ValueError:
        schemes = {
            "web": frozenset({"http", "https"}),
            "api": frozenset({"http", "https", "ws", "wss"}),
            "protocol": frozenset({"http", "https", "ws", "wss"}),
            "database": frozenset({"mysql"}),
            "other": frozenset({"http", "https", "ws", "wss", "mysql"}),
        }[kind]
        raise _url_error(value, allowed_schemes=schemes) from None


def _validate_check_endpoint(value: str) -> str:
    try:
        return validate_check_target(value)
    except ValueError:
        raise _url_error(value, allowed_schemes=frozenset({"http", "https"})) from None


def _reference_parse_error(value: str) -> PydanticCustomError | None:
    """Return the first generic reference safety failure, if any."""
    if _PLACEHOLDER_PATTERN.search(value):
        return PydanticCustomError("unresolved_placeholder", "url contains unresolved placeholder")
    if any(ord(char) <= 0x1F or ord(char) == 0x7F for char in value):
        return PydanticCustomError("url_control_forbidden", "url contains control characters")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return PydanticCustomError("reference_host_invalid", "reference host is invalid")
    if not parsed.scheme:
        return PydanticCustomError("url_absolute_required", "url must be absolute")
    if not hostname or parsed.netloc.rsplit("@", 1)[-1].endswith(":") or (port is not None and not 0 <= port <= 65535):
        return PydanticCustomError("reference_host_invalid", "reference host is invalid")
    if parsed.username is not None or parsed.password is not None:
        return PydanticCustomError("url_userinfo_forbidden", "url userinfo is forbidden")
    if "#" in value:
        return PydanticCustomError("url_fragment_forbidden", "url fragment is forbidden")
    return None


def _validate_reference(value: str, rel: str) -> str:
    try:
        return validate_reference_url(rel, value)  # type: ignore[arg-type]
    except ValueError:
        error = _reference_parse_error(value)
        if error is not None:
            raise error from None
        parsed = urlsplit(value)
        if rel == "studio" and "?" in value:
            raise PydanticCustomError("reference_query_invalid", "reference query is invalid") from None
        if "?" in value:
            raise PydanticCustomError("url_query_forbidden", "url query is forbidden") from None
        allowed = {"docs": {"https"}, "api_docs": {"http", "https"}, "studio": {"https"}}[rel]
        if parsed.scheme not in allowed:
            raise PydanticCustomError("url_scheme_invalid", "url scheme is invalid") from None
        if rel == "api_docs" and parsed.scheme == "http":
            raise PydanticCustomError("reference_host_invalid", "reference host is invalid") from None
        raise PydanticCustomError("reference_query_invalid", "reference query is invalid") from None


class ServiceV2(SpecModel):
    name: str
    kind: Literal["web", "api", "protocol", "database", "other"]
    url: str
    display: Literal["default", "advanced", "hidden"] = "default"
    primary: bool = False
    description: str
    tech: str | None = None
    links: dict[Literal["docs", "api_docs", "studio"], str] = Field(default_factory=dict)

    @field_validator("name", "description")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        return _blank(value)

    @field_validator("url")
    @classmethod
    def _safe_url(cls, value: str, info: ValidationInfo) -> str:
        kind = info.data.get("kind")
        if kind is None:
            return value
        return _validate_service_endpoint(value, kind)

    @field_validator("links")
    @classmethod
    def _safe_links(cls, value: dict[str, str]) -> dict[str, str]:
        errors: list[InitErrorDetails] = []
        for rel, url in value.items():
            try:
                _validate_reference(url, rel)
            except PydanticCustomError as exc:
                errors.append(InitErrorDetails(type=exc, loc=(rel,), input=url))
        if errors:
            raise ValidationError.from_exception_data(cls.__name__, errors)
        return value


class ProcessV2(SpecModel):
    command: tuple[str, ...]
    cwd: str = "."
    provides: tuple[Identifier, ...] | None = None

    @field_validator("command")
    @classmethod
    def _command_must_not_be_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise PydanticCustomError("empty_command", "command must not be empty")
        return value

    @field_validator("cwd")
    @classmethod
    def _safe_cwd(cls, value: str, info: ValidationInfo) -> str:
        return _project_path(value, info, allow_dot=True)


class CheckV2(SpecModel):
    type: Literal["http"] = "http"
    target: str
    timeout: float = 2.0
    attempts: int = Field(default=1, gt=0)
    service: Identifier | None = None

    @field_validator("target")
    @classmethod
    def _safe_target(cls, value: str) -> str:
        return _validate_check_endpoint(value)


class TaskV2(SpecModel):
    command: tuple[str, ...]
    cwd: str = "."
    description: str = ""
    starts: tuple[Identifier, ...] = ()
    stops: tuple[Identifier, ...] = ()

    @field_validator("command")
    @classmethod
    def _command_must_not_be_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise PydanticCustomError("empty_command", "command must not be empty")
        return value

    @field_validator("cwd")
    @classmethod
    def _safe_cwd(cls, value: str, info: ValidationInfo) -> str:
        return _project_path(value, info, allow_dot=True)


class ToolsV2(SpecModel):
    required: tuple[str, ...] = ()

    @field_validator("required")
    @classmethod
    def _safe_unique_tools(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for tool in value:
            try:
                validate_bare_executable(tool)
            except ValueError:
                raise PydanticCustomError("invalid_executable", "tool is invalid") from None
        if len(set(value)) != len(value):
            raise PydanticCustomError("requirement_duplicate", "requirement is duplicated")
        return value


class PathsV2(SpecModel):
    required: tuple[str, ...] = ()

    @field_validator("required")
    @classmethod
    def _safe_unique_paths(cls, value: tuple[str, ...], info: ValidationInfo) -> tuple[str, ...]:
        for path in value:
            _project_path(path, info)
        if len(set(value)) != len(value):
            raise PydanticCustomError("requirement_duplicate", "requirement is duplicated")
        return value


class LifecycleSpecV2(SpecModel):
    _loader_path: Path = PrivateAttr(default=Path("."))
    version: int
    template: str
    name: str
    description: str | None = None
    env_file: str | None = None
    guide: str | None = None
    tools: ToolsV2 = Field(default_factory=ToolsV2)
    paths: PathsV2 = Field(default_factory=PathsV2)
    env: dict[Identifier, EnvRequirement] = Field(default_factory=dict)
    services: dict[Identifier, ServiceV2] = Field(default_factory=dict)
    processes: dict[Identifier, ProcessV2] = Field(default_factory=dict)
    checks: dict[Identifier, CheckV2] = Field(default_factory=dict)
    tasks: dict[Identifier, TaskV2] = Field(default_factory=dict)

    @field_validator("template", "name")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        return _blank(value)

    @field_validator("env_file", "guide")
    @classmethod
    def _safe_root_path(cls, value: str | None, info: ValidationInfo) -> str | None:
        if value is None:
            return None
        return _project_path(value, info)

    @model_validator(mode="after")
    def _validate_contract(self, info: ValidationInfo) -> LifecycleSpecV2:  # noqa: C901
        loader_path = (info.context or {}).get("loader_path")
        if not isinstance(loader_path, Path):
            raise PydanticCustomError("unsafe_project_path", "project path is unsafe")
        if self.version != 2:
            raise PydanticCustomError("unsupported_version", "unsupported version")
        if not self.processes:
            raise PydanticCustomError("missing_processes", "at least one process must be declared")
        primaries = [service for service in self.services.values() if service.primary]
        if self.services and not primaries:
            raise PydanticCustomError("primary_required", "a primary service is required")
        if len(primaries) > 1:
            raise PydanticCustomError("primary_multiple", "multiple primary services are invalid")
        if primaries and primaries[0].display == "hidden":
            raise PydanticCustomError("primary_hidden", "primary service must not be hidden")
        service_ids = set(self.services)
        for process in self.processes.values():
            if process.provides is not None and any(service not in service_ids for service in process.provides):
                raise PydanticCustomError("service_reference_unknown", "service reference is invalid")
        for check_id, check in self.checks.items():
            service = check.service if check.service is not None else check_id if check_id in service_ids else None
            if service is None:
                raise PydanticCustomError("check_service_required", "check service is required")
            if service not in service_ids:
                raise PydanticCustomError("service_reference_unknown", "service reference is invalid")
        for task in self.tasks.values():
            if any(service not in service_ids for service in (*task.starts, *task.stops)):
                raise PydanticCustomError("service_reference_unknown", "service reference is invalid")
        validated = self.model_copy()
        object.__setattr__(validated, "_loader_path", loader_path)
        return validated

    @property
    def path(self) -> Path:
        """Return the loader-owned lifecycle file path."""
        return self._loader_path

    @property
    def required_tools(self) -> tuple[str, ...]:
        return self.tools.required

    @property
    def required_paths(self) -> tuple[str, ...]:
        return self.paths.required


type AuthoredLifecycleSpec = LifecycleSpecV1 | LifecycleSpecV2

# Compatibility aliases stay bound to v1 while newer public annotations use
# AuthoredLifecycleSpec for loaded projects.
LifecycleSpec = LifecycleSpecV1
Service = ServiceV1
Process = ProcessV1
Check = CheckV1
Task = TaskV1


__all__ = [
    "SUPPORTED_LIFECYCLE_VERSION",
    "SUPPORTED_LIFECYCLE_VERSIONS",
    "AuthoredLifecycleSpec",
    "Check",
    "CheckV1",
    "CheckV2",
    "EnvRequirement",
    "LifecycleSpec",
    "LifecycleSpecV1",
    "LifecycleSpecV2",
    "Process",
    "ProcessV1",
    "ProcessV2",
    "RequiredList",
    "Service",
    "ServiceV1",
    "ServiceV2",
    "SpecModel",
    "Task",
    "TaskV1",
    "TaskV2",
]
