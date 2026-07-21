from __future__ import annotations

from pathlib import Path

import pytest
import typer
from pydantic import ValidationError

from agentseek.cli.lifecycle.spec import (
    Check,
    CheckV1,
    LifecycleSpec,
    LifecycleSpecV1,
    Process,
    ProcessV1,
    Service,
    ServiceV1,
    Task,
    TaskV1,
    load_lifecycle_spec,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "lifecycle"


def _valid_spec_data() -> dict[str, object]:
    return {
        "path": Path("loader.toml"),
        "version": 1,
        "name": "Project",
        "processes": {"app": {"command": ["python", "-m", "http.server"]}},
    }


def _coercible_text() -> str:
    return (FIXTURES / "v1-coercible.toml").read_text(encoding="utf-8")


def test_loads_minimal_v1_spec_with_default_template() -> None:
    path = FIXTURES / "v1-minimal.toml"

    spec = load_lifecycle_spec(path)

    assert isinstance(spec, LifecycleSpecV1)
    assert spec.template == ""
    assert spec.processes["app"].command == ("python", "-m", "http.server")


@pytest.mark.parametrize("version", ['"1"', "1.0", "true"])
def test_load_coerces_existing_v1_values(tmp_path: Path, version: str) -> None:
    path = tmp_path / "lifecycle.toml"
    path.write_text(_coercible_text().replace('version = "1"', f"version = {version}"), encoding="utf-8")

    spec = load_lifecycle_spec(path)

    assert isinstance(spec, LifecycleSpecV1)
    assert spec.version == 1
    assert spec.env["API_KEY"].required is True
    assert spec.checks["app"].timeout == 2.5
    assert spec.checks["app"].attempts == 2


def test_direct_v1_models_preserve_existing_defaults_and_collections() -> None:
    data = _valid_spec_data()
    data["name"] = "   "
    data["tools"] = {"required": ["python"]}
    data["paths"] = {"required": ["pyproject.toml"]}
    data["env"] = {"API_KEY": {"aliases": ["LEGACY_API_KEY"]}}
    data["tasks"] = {"print": {"command": ["python", "-c", "print('ok')"]}}

    spec = LifecycleSpecV1.model_validate(data)

    assert spec.template == ""
    assert spec.name == "   "
    assert spec.tools.required == ("python",)
    assert spec.paths.required == ("pyproject.toml",)
    assert spec.env["API_KEY"].aliases == ("LEGACY_API_KEY",)
    assert spec.processes["app"].command == ("python", "-m", "http.server")
    assert spec.tasks["print"].command == ("python", "-c", "print('ok')")


def test_v1_public_models_remain_compatibility_aliases() -> None:
    assert LifecycleSpec is LifecycleSpecV1
    assert Service is ServiceV1
    assert Process is ProcessV1
    assert Check is CheckV1
    assert Task is TaskV1


@pytest.mark.parametrize(
    ("location", "extra"),
    [
        ((), {"unexpected": "value"}),
        (("services", "app"), {"services": {"app": {"url": "http://127.0.0.1:8000", "unexpected": "value"}}}),
        (("processes", "app"), {"processes": {"app": {"command": ["python"], "unexpected": "value"}}}),
        (("checks", "app"), {"checks": {"app": {"target": "http://127.0.0.1:8000", "unexpected": "value"}}}),
        (("tasks", "print"), {"tasks": {"print": {"command": ["python"], "unexpected": "value"}}}),
        (("env", "API_KEY"), {"env": {"API_KEY": {"unexpected": "value"}}}),
    ],
)
def test_direct_v1_models_reject_unknown_fields(location: tuple[str, ...], extra: dict[str, object]) -> None:
    data = _valid_spec_data()
    data.update(extra)

    with pytest.raises(ValidationError) as exc_info:
        LifecycleSpecV1.model_validate(data)

    errors = exc_info.value.errors()
    assert any(error["type"] == "extra_forbidden" and error["loc"][: len(location)] == location for error in errors)


@pytest.mark.parametrize(
    ("marker", "insertion"),
    [
        ('name = "Coercible Project"', 'unexpected = "value"'),
        ('url = "http://127.0.0.1:8000"', 'unexpected = "value"'),
        ('command = ["python", "-m", "http.server"]', 'unexpected = "value"'),
        ('target = "http://127.0.0.1:8000"', 'unexpected = "value"'),
        ('command = ["python", "-c", "print(\'ok\')"]', 'unexpected = "value"'),
        ('aliases = ["LEGACY_API_KEY"]', 'unexpected = "value"'),
    ],
)
def test_toml_v1_rejects_unknown_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], marker: str, insertion: str
) -> None:
    path = tmp_path / "lifecycle.toml"
    path.write_text(_coercible_text().replace(marker, f"{marker}\n{insertion}"), encoding="utf-8")

    with pytest.raises(typer.Exit) as exc_info:
        load_lifecycle_spec(path)

    assert exc_info.value.exit_code == 2
    assert "extra_forbidden" in capsys.readouterr().err


@pytest.mark.parametrize("section", ["processes", "tasks"])
def test_direct_v1_models_reject_empty_commands(section: str) -> None:
    data = _valid_spec_data()
    data[section] = {"app": {"command": []}}

    with pytest.raises(ValidationError) as exc_info:
        LifecycleSpecV1.model_validate(data)

    assert any(error["type"] == "empty_command" for error in exc_info.value.errors())


@pytest.mark.parametrize("section", ["processes", "tasks"])
def test_direct_v1_models_reject_numeric_command_items(section: str) -> None:
    data = _valid_spec_data()
    data[section] = {"app": {"command": ["python", 3]}}

    with pytest.raises(ValidationError) as exc_info:
        LifecycleSpecV1.model_validate(data)

    assert any(error["type"] == "string_type" for error in exc_info.value.errors())


@pytest.mark.parametrize("section", ["processes", "tasks"])
def test_direct_v1_models_reject_path_cwds(section: str) -> None:
    data = _valid_spec_data()
    data[section] = {"app": {"command": ["python"], "cwd": Path("nested")}}

    with pytest.raises(ValidationError) as exc_info:
        LifecycleSpecV1.model_validate(data)

    assert any(error["type"] == "string_type" for error in exc_info.value.errors())


def test_loader_owned_path_cannot_be_overridden_by_authored_toml(tmp_path: Path) -> None:
    path = tmp_path / "lifecycle.toml"
    path.write_text(
        _coercible_text().replace('name = "Coercible Project"', 'path = "authored.toml"\nname = "Coercible Project"'),
        encoding="utf-8",
    )

    spec = load_lifecycle_spec(path)

    assert spec.path == path
