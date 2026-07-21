"""Authored lifecycle v1 models."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

SUPPORTED_LIFECYCLE_VERSION = 1


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
        if self.version != SUPPORTED_LIFECYCLE_VERSION:
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


LifecycleSpec = LifecycleSpecV1
Service = ServiceV1
Process = ProcessV1
Check = CheckV1
Task = TaskV1


__all__ = [
    "SUPPORTED_LIFECYCLE_VERSION",
    "Check",
    "CheckV1",
    "EnvRequirement",
    "LifecycleSpec",
    "LifecycleSpecV1",
    "Process",
    "ProcessV1",
    "RequiredList",
    "Service",
    "ServiceV1",
    "SpecModel",
    "Task",
    "TaskV1",
]
