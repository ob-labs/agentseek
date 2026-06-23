"""Lifecycle spec loading."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from pydantic_core import PydanticCustomError

from agentseek.cli.lifecycle.errors import exit_project_error

SUPPORTED_LIFECYCLE_VERSION = 1
LIFECYCLE_SPEC_FILE = ".agentseek/lifecycle.toml"
REQUIRED_COMMANDS: tuple[str, ...] = ("dev", "info", "doctor")


class SpecModel(BaseModel):
    """Base model for lifecycle spec sections."""

    model_config = ConfigDict(extra="ignore", frozen=True)


class RequiredOptional(SpecModel):
    required: tuple[str, ...] = ()
    optional: tuple[str, ...] = ()

    def as_requirement_map(self) -> dict[str, bool]:
        values = dict.fromkeys(self.required, True)
        values.update({name: False for name in self.optional if name not in values})
        return values


class EnvRequirement(SpecModel):
    required: bool = False
    secret: bool = False
    description: str = ""
    aliases: tuple[str, ...] = ()

    def keys(self, name: str) -> tuple[str, ...]:
        return (name, *self.aliases)


class Service(SpecModel):
    url: str


class Process(SpecModel):
    command: tuple[str, ...]
    cwd: str = "."
    env: dict[str, str] = Field(default_factory=dict)
    shutdown_grace_seconds: int = 10

    @field_validator("command")
    @classmethod
    def _command_must_not_be_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise PydanticCustomError("empty_command", "command must not be empty")
        return value


class Check(SpecModel):
    type: Literal["http", "tcp"] = "tcp"
    target: str
    required: bool = True
    timeout: float = 2.0
    attempts: int = 1
    wait: float = 0.0


class Task(SpecModel):
    command: tuple[str, ...]
    cwd: str = "."
    description: str = ""

    @field_validator("command")
    @classmethod
    def _command_must_not_be_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise PydanticCustomError("empty_command", "command must not be empty")
        return value


class LifecycleSpec(SpecModel):
    path: Path
    version: int
    template: str = ""
    name: str = ""
    tools: RequiredOptional = Field(default_factory=RequiredOptional)
    paths: RequiredOptional = Field(default_factory=RequiredOptional)
    env: dict[str, EnvRequirement] = Field(default_factory=dict)
    services: dict[str, Service] = Field(default_factory=dict)
    processes: dict[str, Process] = Field(default_factory=dict)
    checks: dict[str, Check] = Field(default_factory=dict)
    tasks: dict[str, Task] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_contract(self) -> LifecycleSpec:
        if self.version != SUPPORTED_LIFECYCLE_VERSION:
            raise PydanticCustomError("unsupported_version", "unsupported version {version}", {"version": self.version})
        if not self.name:
            raise PydanticCustomError("missing_name", "name must be set")
        if not self.processes:
            raise PydanticCustomError("missing_processes", "at least one process must be declared")
        return self

    @property
    def tool_requirements(self) -> dict[str, bool]:
        return self.tools.as_requirement_map()

    @property
    def path_requirements(self) -> dict[str, bool]:
        return self.paths.as_requirement_map()


def load_lifecycle_spec(path: Path) -> LifecycleSpec:
    """Load and validate a lifecycle spec from TOML."""
    try:
        data: dict[str, Any] = tomllib.loads(path.read_text(encoding="utf-8"))
        return LifecycleSpec.model_validate({**data, "path": path})
    except ValidationError as exc:
        exit_project_error("Invalid AgentSeek lifecycle spec.", str(exc))
    except tomllib.TOMLDecodeError as exc:
        exit_project_error("Invalid AgentSeek lifecycle TOML.", str(exc))


__all__ = [
    "LIFECYCLE_SPEC_FILE",
    "REQUIRED_COMMANDS",
    "SUPPORTED_LIFECYCLE_VERSION",
    "Check",
    "EnvRequirement",
    "LifecycleSpec",
    "Process",
    "Service",
    "Task",
    "load_lifecycle_spec",
]
