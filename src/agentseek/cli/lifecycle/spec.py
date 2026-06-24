"""Lifecycle spec loading."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, ClassVar, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from pydantic_core import PydanticCustomError
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource

from agentseek.cli.lifecycle.errors import exit_project_error

SUPPORTED_LIFECYCLE_VERSION = 1
LIFECYCLE_SPEC_FILE = ".agentseek/lifecycle.toml"
REQUIRED_COMMANDS: tuple[str, ...] = ("dev", "info", "doctor")


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


class Service(SpecModel):
    url: str


class Process(SpecModel):
    command: tuple[str, ...]
    cwd: str = "."

    @field_validator("command")
    @classmethod
    def _command_must_not_be_empty(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if not value:
            raise PydanticCustomError("empty_command", "command must not be empty")
        return value


class Check(SpecModel):
    type: Literal["http"] = "http"
    target: str
    timeout: float = 2.0
    attempts: int = 1


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


class LifecycleSpec(BaseSettings):
    model_config = SettingsConfigDict(extra="forbid", frozen=True)

    toml_file: ClassVar[Path]
    path: Path
    version: int
    template: str = ""
    name: str = ""
    env_file: str | None = None
    tools: RequiredList = Field(default_factory=RequiredList)
    paths: RequiredList = Field(default_factory=RequiredList)
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
    def required_tools(self) -> tuple[str, ...]:
        return self.tools.required

    @property
    def required_paths(self) -> tuple[str, ...]:
        return self.paths.required

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        del env_settings, dotenv_settings, file_secret_settings
        return (init_settings, TomlConfigSettingsSource(settings_cls, toml_file=cls.toml_file))


def load_lifecycle_spec(path: Path) -> LifecycleSpec:
    """Load and validate a lifecycle spec from TOML."""
    spec_settings = cast(
        Any,
        type(
            "LifecycleSpecSettings",
            (LifecycleSpec,),
            {
                "__annotations__": {"toml_file": ClassVar[Path]},
                "toml_file": path,
            },
        ),
    )
    try:
        return spec_settings(path=path)
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
