"""Machine-readable lifecycle command handlers."""

from __future__ import annotations

import typer

from agentseek.cli.lifecycle.core import discover_lifecycle_project
from agentseek.cli.lifecycle.diagnostics import evaluate_doctor_json
from agentseek.cli.lifecycle.errors import (
    LifecycleInputError,
    LifecycleNotFoundError,
    LifecycleTomlError,
    LifecycleValidationError,
    LifecycleVersionUnsupportedError,
)
from agentseek.cli.lifecycle.json_output import (
    CliOptionConflictDetailsDTO,
    DoctorErrorEnvelopeDTO,
    DoctorSuccessEnvelopeDTO,
    EmptyErrorDetailsDTO,
    ErrorDTO,
    InfoDataDTO,
    InfoErrorEnvelopeDTO,
    InfoSuccessEnvelopeDTO,
    TomlErrorDetailsDTO,
    UnsupportedVersionDetailsDTO,
    ValidationErrorDetailsDTO,
    ValidationIssueDTO,
    serialize_json,
)
from agentseek.cli.lifecycle.normalize import normalize_lifecycle


def _lifecycle_error_dto(error: LifecycleInputError) -> tuple[int | None, ErrorDTO]:
    if isinstance(error, LifecycleNotFoundError):
        return None, ErrorDTO(
            code="lifecycle_not_found",
            message="No lifecycle.toml was found.",
            details=EmptyErrorDetailsDTO(),
        )
    if isinstance(error, LifecycleTomlError):
        return None, ErrorDTO(
            code="lifecycle_toml_invalid",
            message="The lifecycle TOML is invalid.",
            details=TomlErrorDetailsDTO(line=error.line, column=error.column),
        )
    if isinstance(error, LifecycleValidationError):
        issues = tuple(
            ValidationIssueDTO(path=issue.path, code=issue.code, message=issue.message) for issue in error.issues
        )
        return error.lifecycle_version, ErrorDTO(
            code="lifecycle_validation_failed",
            message="The lifecycle specification is invalid.",
            details=ValidationErrorDetailsDTO(issues=issues),
        )
    if isinstance(error, LifecycleVersionUnsupportedError):
        return error.found, ErrorDTO(
            code="lifecycle_version_unsupported",
            message="The lifecycle version is unsupported.",
            details=UnsupportedVersionDetailsDTO(found=error.found, supported=(1, 2)),
        )
    raise TypeError


def print_info_json() -> None:
    """Write exactly one info envelope and preserve JSON-mode exit semantics."""
    lifecycle_version: int | None = None
    try:
        try:
            project = discover_lifecycle_project()
            lifecycle_version = project.spec.version
            normalized = normalize_lifecycle(project.spec, project_root=project.root)
            envelope = InfoSuccessEnvelopeDTO(
                lifecycle_version=normalized.lifecycle_version,
                data=InfoDataDTO.from_normalized(normalized),
            )
            output = serialize_json(envelope)
            exit_code = 0
        except LifecycleInputError as error:
            lifecycle_version, error_dto = _lifecycle_error_dto(error)
            envelope = InfoErrorEnvelopeDTO(
                lifecycle_version=lifecycle_version,
                error=error_dto,
            )
            output = serialize_json(envelope)
            exit_code = 2
    except Exception:
        envelope = InfoErrorEnvelopeDTO(
            lifecycle_version=lifecycle_version,
            error=ErrorDTO(
                code="internal_error",
                message="Unexpected internal error.",
                details=EmptyErrorDetailsDTO(),
            ),
        )
        output = serialize_json(envelope)
        exit_code = 1
    typer.echo(output, nl=False)
    if exit_code:
        raise typer.Exit(exit_code)


def print_doctor_json(*, live: bool, strict: bool) -> None:
    """Write one doctor envelope from normalized diagnostic inputs."""
    lifecycle_version: int | None = None
    try:
        if strict:
            envelope = DoctorErrorEnvelopeDTO(
                lifecycle_version=None,
                error=ErrorDTO(
                    code="cli_option_conflict",
                    message="Options --strict and --json cannot be combined.",
                    details=CliOptionConflictDetailsDTO(options=("--json", "--strict")),
                ),
            )
            output = serialize_json(envelope)
            exit_code = 2
        else:
            try:
                project = discover_lifecycle_project()
                lifecycle_version = project.spec.version
                normalized = normalize_lifecycle(project.spec, project_root=project.root)
                data = evaluate_doctor_json(project.root, normalized, live=live)
                envelope = DoctorSuccessEnvelopeDTO(lifecycle_version=normalized.lifecycle_version, data=data)
                output = serialize_json(envelope)
                exit_code = 0 if data.passed else 1
            except LifecycleInputError as error:
                lifecycle_version, error_dto = _lifecycle_error_dto(error)
                envelope = DoctorErrorEnvelopeDTO(
                    lifecycle_version=lifecycle_version,
                    error=error_dto,
                )
                output = serialize_json(envelope)
                exit_code = 2
    except Exception:
        envelope = DoctorErrorEnvelopeDTO(
            lifecycle_version=lifecycle_version,
            error=ErrorDTO(
                code="internal_error",
                message="Unexpected internal error.",
                details=EmptyErrorDetailsDTO(),
            ),
        )
        output = serialize_json(envelope)
        exit_code = 1
    typer.echo(output, nl=False)
    if exit_code:
        raise typer.Exit(exit_code)


__all__ = ["print_doctor_json", "print_info_json"]
