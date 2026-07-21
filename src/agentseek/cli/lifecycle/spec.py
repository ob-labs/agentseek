"""Lifecycle spec loading."""

from __future__ import annotations

import tomllib
from pathlib import Path

from pydantic import ValidationError

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
from agentseek.cli.lifecycle.errors import exit_project_error

LIFECYCLE_SPEC_FILE = ".agentseek/lifecycle.toml"
REQUIRED_COMMANDS: tuple[str, ...] = ("dev", "info", "doctor")


def load_lifecycle_spec(path: Path) -> LifecycleSpec:
    """Load and validate a lifecycle spec from TOML."""
    try:
        with path.open("rb") as file:
            data = tomllib.load(file)
        return LifecycleSpecV1.model_validate({**data, "path": path})
    except ValidationError as exc:
        exit_project_error("Invalid AgentSeek lifecycle spec.", str(exc))
    except tomllib.TOMLDecodeError as exc:
        exit_project_error("Invalid AgentSeek lifecycle TOML.", str(exc))


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
    "load_lifecycle_spec",
]
