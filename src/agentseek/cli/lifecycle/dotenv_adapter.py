"""Strict lifecycle adapter around the bounded python-dotenv implementation APIs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from dotenv.parser import parse_stream
from dotenv.variables import parse_variables


class LifecycleDotenvError(ValueError):
    def __init__(self, path: Path, message: str, *, line: int | None = None) -> None:
        self.path = path
        self.line = line
        location = f" at line {line}" if line is not None else ""
        super().__init__(f"Lifecycle env file '{path}' {message}{location}.")


def parse_lifecycle_dotenv(
    path: Path,
    *,
    ambient: Mapping[str, str],
) -> dict[str, str | None]:
    try:
        with path.open(encoding="utf-8") as stream:
            bindings = list(parse_stream(stream))
    except FileNotFoundError as exc:
        raise LifecycleDotenvError(path, "does not exist") from exc
    except UnicodeDecodeError as exc:
        raise LifecycleDotenvError(path, "is not valid UTF-8") from exc
    except OSError as exc:
        reason = exc.strerror or type(exc).__name__
        raise LifecycleDotenvError(path, f"could not be read: {reason}") from exc

    malformed = next((binding for binding in bindings if binding.error), None)
    if malformed is not None:
        raise LifecycleDotenvError(
            path,
            "has malformed dotenv syntax",
            line=malformed.original.line,
        )

    context: dict[str, str | None] = dict(ambient)
    values: dict[str, str | None] = {}
    for binding in bindings:
        if binding.key is None:
            continue
        if "\x00" in binding.key or "=" in binding.key:
            raise LifecycleDotenvError(
                path,
                "has an invalid variable name",
                line=binding.original.line,
            )
        value = (
            None if binding.value is None else "".join(atom.resolve(context) for atom in parse_variables(binding.value))
        )
        if value is not None and "\x00" in value:
            raise LifecycleDotenvError(
                path,
                "contains a NUL character in a resolved value",
                line=binding.original.line,
            )
        values[binding.key] = value
        context[binding.key] = value
    return values
