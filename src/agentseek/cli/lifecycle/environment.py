"""Immutable environment boundary for AgentSeek-managed lifecycle processes."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from types import MappingProxyType

from agentseek.cli.lifecycle.dotenv_adapter import (
    LifecycleDotenvError,
    parse_lifecycle_dotenv,
)

_MISMATCHED_SNAPSHOT_KEYS_ERROR = "Snapshot values and origins must contain the same keys."


class EnvironmentOrigin(StrEnum):
    """Value-free provenance retained by the lifecycle owner."""

    ENV_FILE = "env_file"
    LAUNCH_ENVIRONMENT = "launch_environment"


@dataclass(frozen=True)
class LifecycleEnvironmentSnapshot:
    """Resolved child values that cannot be changed after construction."""

    values: Mapping[str, str] = field(repr=False)
    origins: Mapping[str, EnvironmentOrigin]

    def __post_init__(self) -> None:
        values = dict(self.values)
        origins = dict(self.origins)
        if values.keys() != origins.keys():
            raise ValueError(_MISMATCHED_SNAPSHOT_KEYS_ERROR)
        object.__setattr__(self, "values", MappingProxyType(values))
        object.__setattr__(self, "origins", MappingProxyType(origins))

    def as_subprocess_env(self) -> dict[str, str]:
        """Return an isolated mutable mapping accepted by subprocess APIs."""

        return dict(self.values)


def resolve_lifecycle_environment(
    *,
    env_file: Path | None,
    launch_environment: Mapping[str, str] | None = None,
) -> LifecycleEnvironmentSnapshot:
    """Resolve dotenv plus the non-empty launch overlay exactly once."""

    captured_launch = dict(os.environ if launch_environment is None else launch_environment)
    file_values = parse_lifecycle_dotenv(env_file, ambient=captured_launch) if env_file is not None else {}
    values: dict[str, str] = {}
    origins: dict[str, EnvironmentOrigin] = {}

    for key, value in file_values.items():
        if value is None:
            continue
        values[key] = value
        origins[key] = EnvironmentOrigin.ENV_FILE

    for key, value in captured_launch.items():
        if value == "":
            continue
        values[key] = value
        origins[key] = EnvironmentOrigin.LAUNCH_ENVIRONMENT

    return LifecycleEnvironmentSnapshot(values=values, origins=origins)


__all__ = [
    "EnvironmentOrigin",
    "LifecycleDotenvError",
    "LifecycleEnvironmentSnapshot",
    "resolve_lifecycle_environment",
]
