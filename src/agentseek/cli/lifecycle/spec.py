"""Lifecycle spec loading."""

from __future__ import annotations

import tomllib
from pathlib import Path
from re import fullmatch
from typing import Final

from pydantic import ValidationError
from pydantic_core import ErrorDetails

from agentseek.cli.lifecycle.authored import (
    SUPPORTED_LIFECYCLE_VERSION,
    Check,
    CheckV1,
    EnvRequirement,
    LifecycleSpec,
    LifecycleSpecV1,
    Process,
    ProcessV1,
    Service,
    ServiceV1,
    Task,
    TaskV1,
)
from agentseek.cli.lifecycle.errors import (
    LifecycleTomlError,
    LifecycleValidationError,
    LifecycleValidationIssue,
    LifecycleVersionUnsupportedError,
    exit_project_error,
)

LIFECYCLE_SPEC_FILE = ".agentseek/lifecycle.toml"
REQUIRED_COMMANDS: tuple[str, ...] = ("dev", "info", "doctor")
SUPPORTED_DISCOVERY_LIFECYCLE_VERSIONS: tuple[int, ...] = (1, 2)

_VALID_IDENTIFIER = r"[A-Za-z0-9][A-Za-z0-9_-]*"
_ISSUE_MAPPING: Final[dict[str, tuple[str, str]]] = {
    "missing": ("field_required", "Required field is missing."),
    "extra_forbidden": ("field_forbidden", "Field is not allowed."),
    "string_type": ("type_invalid", "Value has an invalid type."),
    "bool_type": ("type_invalid", "Value has an invalid type."),
    "bool_parsing": ("type_invalid", "Value has an invalid type."),
    "int_type": ("type_invalid", "Value has an invalid type."),
    "int_parsing": ("type_invalid", "Value has an invalid type."),
    "int_from_float": ("type_invalid", "Value has an invalid type."),
    "float_type": ("type_invalid", "Value has an invalid type."),
    "float_parsing": ("type_invalid", "Value has an invalid type."),
    "finite_number": ("type_invalid", "Value has an invalid type."),
    "tuple_type": ("type_invalid", "Value has an invalid type."),
    "list_type": ("type_invalid", "Value has an invalid type."),
    "dict_type": ("type_invalid", "Value has an invalid type."),
    "model_type": ("type_invalid", "Value has an invalid type."),
    "literal_error": ("literal_invalid", "Value is not an allowed choice."),
    "greater_than": ("number_not_positive", "Value must be greater than zero."),
    "empty_command": ("command_empty", "Command must not be empty."),
    "missing_name": ("value_blank", "Value must not be blank."),
    "blank_value": ("value_blank", "Value must not be blank."),
    "missing_processes": ("process_required", "At least one process must be declared."),
    "invalid_identifier": ("identifier_invalid", "Identifier has an invalid format."),
    "invalid_executable": ("tool_invalid", "Required tool is not a safe executable name."),
    "unsafe_project_path": ("path_unsafe", "Project path is unsafe."),
    "unresolved_placeholder": ("placeholder_unresolved", "Value contains an unresolved placeholder."),
    "url_absolute_required": ("url_invalid", "URL is invalid."),
    "url_host_required": ("url_invalid", "URL is invalid."),
    "reference_host_invalid": ("url_invalid", "URL is invalid."),
    "url_scheme_invalid": ("url_scheme_invalid", "URL scheme is not allowed."),
    "url_control_forbidden": ("url_component_forbidden", "URL contains a forbidden component."),
    "url_userinfo_forbidden": ("url_component_forbidden", "URL contains a forbidden component."),
    "url_query_forbidden": ("url_component_forbidden", "URL contains a forbidden component."),
    "url_fragment_forbidden": ("url_component_forbidden", "URL contains a forbidden component."),
    "reference_query_invalid": ("reference_query_invalid", "Reference query is not allowed."),
    "requirement_duplicate": ("requirement_duplicate", "Requirement is duplicated."),
    "primary_required": ("primary_required", "Exactly one primary service is required."),
    "primary_multiple": ("primary_multiple", "Only one primary service is allowed."),
    "primary_hidden": ("primary_hidden", "Primary service must not be hidden."),
    "service_reference_unknown": ("service_reference_unknown", "Referenced service does not exist."),
    "check_service_required": ("check_service_missing", "Check must be associated with a service."),
}
_DEFAULT_ISSUE: Final[tuple[str, str]] = ("value_invalid", "Value is invalid.")


def _validation_issue_path(loc: tuple[str | int, ...]) -> str:
    """Return a safe public path for a Pydantic validation location."""
    path = "$"
    for segment in loc:
        if segment == "__root__":
            continue
        if isinstance(segment, int):
            path = f"{path}[{segment}]"
        elif fullmatch(_VALID_IDENTIFIER, segment):
            path = segment if path == "$" else f"{path}.{segment}"
        else:
            path = "<invalid-id>" if path == "$" else f"{path}.<invalid-id>"
    return path


def _validation_issue(error: ErrorDetails) -> LifecycleValidationIssue:
    """Map one Pydantic error to the stable, redacted public contract."""
    code, message = _ISSUE_MAPPING.get(error["type"], _DEFAULT_ISSUE)
    return LifecycleValidationIssue(_validation_issue_path(error["loc"]), code, message)


def _lifecycle_version(data: dict[str, object]) -> int | None:
    version = data.get("version")
    return version if isinstance(version, int) and not isinstance(version, bool) else None


def read_lifecycle_spec(path: Path, *, project_root: Path) -> LifecycleSpecV1:
    """Read and validate lifecycle TOML without producing CLI output."""
    del project_root
    try:
        with path.open("rb") as file:
            data = tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        raise LifecycleTomlError(
            line=getattr(exc, "lineno", None),
            column=getattr(exc, "colno", None),
            legacy_detail=str(exc),
        ) from exc

    try:
        return LifecycleSpecV1.model_validate({**data, "path": path})
    except ValidationError as exc:
        errors = exc.errors(include_url=False, include_context=False, include_input=False)
        unsupported = next((error for error in errors if error["type"] == "unsupported_version"), None)
        if unsupported is not None:
            raise LifecycleVersionUnsupportedError(
                found=_lifecycle_version(data),
                supported=SUPPORTED_DISCOVERY_LIFECYCLE_VERSIONS,
                legacy_detail=str(exc),
            ) from exc
        issues = tuple(sorted((_validation_issue(error) for error in errors), key=lambda issue: (issue.path, issue.code, issue.message)))
        raise LifecycleValidationError(
            lifecycle_version=_lifecycle_version(data),
            issues=issues,
            legacy_detail=str(exc),
        ) from exc


def load_lifecycle_spec(path: Path) -> LifecycleSpec:
    """Load and validate a lifecycle spec from TOML."""
    try:
        return read_lifecycle_spec(path, project_root=path.parent.parent)
    except LifecycleTomlError as exc:
        exit_project_error("Invalid AgentSeek lifecycle TOML.", exc.legacy_detail)
    except (LifecycleValidationError, LifecycleVersionUnsupportedError) as exc:
        exit_project_error("Invalid AgentSeek lifecycle spec.", exc.legacy_detail)


__all__ = [
    "LIFECYCLE_SPEC_FILE",
    "REQUIRED_COMMANDS",
    "SUPPORTED_LIFECYCLE_VERSION",
    "Check",
    "CheckV1",
    "EnvRequirement",
    "LifecycleSpec",
    "LifecycleSpecV1",
    "Process",
    "ProcessV1",
    "Service",
    "ServiceV1",
    "Task",
    "TaskV1",
    "_validation_issue",
    "_validation_issue_path",
    "load_lifecycle_spec",
    "read_lifecycle_spec",
]
