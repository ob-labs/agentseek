from __future__ import annotations

from pathlib import Path

import pytest
import typer
from pydantic import ValidationError

from agentseek.cli.lifecycle.core import discover_lifecycle_project
from agentseek.cli.lifecycle.errors import (
    LifecycleNotFoundError,
    LifecycleTomlError,
    LifecycleValidationError,
    LifecycleValidationIssue,
    LifecycleVersionUnsupportedError,
)
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
    _validation_issue,
    _validation_issue_path,
    load_lifecycle_spec,
    read_lifecycle_spec,
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


def test_non_emitting_discovery_raises_typed_not_found_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(LifecycleNotFoundError) as exc_info:
        discover_lifecycle_project(tmp_path)

    assert exc_info.value.code == "lifecycle_not_found"
    assert exc_info.value.legacy_detail == "Add .agentseek/lifecycle.toml."
    assert capsys.readouterr() == ("", "")


def test_non_emitting_read_raises_typed_toml_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "lifecycle.toml"
    path.write_text("version = [\n", encoding="utf-8")

    with pytest.raises(LifecycleTomlError) as exc_info:
        read_lifecycle_spec(path, project_root=tmp_path)

    assert exc_info.value.code == "lifecycle_toml_invalid"
    assert exc_info.value.line is None
    assert exc_info.value.column is None
    assert exc_info.value.legacy_detail
    assert capsys.readouterr() == ("", "")


def test_non_emitting_read_raises_typed_unsupported_version_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "lifecycle.toml"
    path.write_text('version = 3\nname = "Project"\n[processes.app]\ncommand = ["python"]\n', encoding="utf-8")

    with pytest.raises(LifecycleVersionUnsupportedError) as exc_info:
        read_lifecycle_spec(path, project_root=tmp_path)

    assert exc_info.value.code == "lifecycle_version_unsupported"
    assert exc_info.value.found == 3
    assert exc_info.value.supported == (1, 2)
    assert exc_info.value.legacy_detail
    assert capsys.readouterr() == ("", "")


def test_non_emitting_read_raises_typed_validation_error_for_selected_model_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "lifecycle.toml"
    path.write_text(
        'version = 1\nname = ""\nunexpected = "value"\n[processes.app]\ncommand = []\n', encoding="utf-8"
    )

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(path, project_root=tmp_path)

    assert exc_info.value.code == "lifecycle_validation_failed"
    assert exc_info.value.lifecycle_version == 1
    assert exc_info.value.issues == (
        LifecycleValidationIssue("processes.app.command", "command_empty", "Command must not be empty."),
        LifecycleValidationIssue("unexpected", "field_forbidden", "Field is not allowed."),
    )
    assert exc_info.value.legacy_detail
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    ("error_type", "code", "message"),
    [
        ("missing", "field_required", "Required field is missing."),
        ("extra_forbidden", "field_forbidden", "Field is not allowed."),
        ("string_type", "type_invalid", "Value has an invalid type."),
        ("bool_type", "type_invalid", "Value has an invalid type."),
        ("bool_parsing", "type_invalid", "Value has an invalid type."),
        ("int_type", "type_invalid", "Value has an invalid type."),
        ("int_parsing", "type_invalid", "Value has an invalid type."),
        ("int_from_float", "type_invalid", "Value has an invalid type."),
        ("float_type", "type_invalid", "Value has an invalid type."),
        ("float_parsing", "type_invalid", "Value has an invalid type."),
        ("finite_number", "type_invalid", "Value has an invalid type."),
        ("tuple_type", "type_invalid", "Value has an invalid type."),
        ("list_type", "type_invalid", "Value has an invalid type."),
        ("dict_type", "type_invalid", "Value has an invalid type."),
        ("model_type", "type_invalid", "Value has an invalid type."),
        ("literal_error", "literal_invalid", "Value is not an allowed choice."),
        ("greater_than", "number_not_positive", "Value must be greater than zero."),
        ("empty_command", "command_empty", "Command must not be empty."),
        ("missing_name", "value_blank", "Value must not be blank."),
        ("blank_value", "value_blank", "Value must not be blank."),
        ("missing_processes", "process_required", "At least one process must be declared."),
        ("invalid_identifier", "identifier_invalid", "Identifier has an invalid format."),
        ("invalid_executable", "tool_invalid", "Required tool is not a safe executable name."),
        ("unsafe_project_path", "path_unsafe", "Project path is unsafe."),
        ("unresolved_placeholder", "placeholder_unresolved", "Value contains an unresolved placeholder."),
        ("url_absolute_required", "url_invalid", "URL is invalid."),
        ("url_host_required", "url_invalid", "URL is invalid."),
        ("reference_host_invalid", "url_invalid", "URL is invalid."),
        ("url_scheme_invalid", "url_scheme_invalid", "URL scheme is not allowed."),
        ("url_control_forbidden", "url_component_forbidden", "URL contains a forbidden component."),
        ("url_userinfo_forbidden", "url_component_forbidden", "URL contains a forbidden component."),
        ("url_query_forbidden", "url_component_forbidden", "URL contains a forbidden component."),
        ("url_fragment_forbidden", "url_component_forbidden", "URL contains a forbidden component."),
        ("reference_query_invalid", "reference_query_invalid", "Reference query is not allowed."),
        ("requirement_duplicate", "requirement_duplicate", "Requirement is duplicated."),
        ("primary_required", "primary_required", "Exactly one primary service is required."),
        ("primary_multiple", "primary_multiple", "Only one primary service is allowed."),
        ("primary_hidden", "primary_hidden", "Primary service must not be hidden."),
        ("service_reference_unknown", "service_reference_unknown", "Referenced service does not exist."),
        ("check_service_required", "check_service_missing", "Check must be associated with a service."),
        ("unknown_error", "value_invalid", "Value is invalid."),
    ],
)
def test_typed_error_mapping_is_application_owned(error_type: str, code: str, message: str) -> None:
    issue = _validation_issue({"type": error_type, "loc": ("services", "app", "url"), "msg": "rejected input"})

    assert issue == LifecycleValidationIssue("services.app.url", code, message)


@pytest.mark.parametrize(
    ("location", "path"),
    [
        (("name",), "name"),
        (("services", "app_1", "url"), "services.app_1.url"),
        (("processes", "app", "command", 1), "processes.app.command[1]"),
        (("services", "bad\x1fkey", "url"), "services.<invalid-id>.url"),
        ((), "$"),
        (("__root__",), "$"),
    ],
)
def test_typed_error_paths_are_safe_and_deterministic(location: tuple[str | int, ...], path: str) -> None:
    assert _validation_issue_path(location) == path


def test_typed_error_issues_redact_rejected_input_literals(tmp_path: Path) -> None:
    secret = "UNIQUE_SECRET_MARKER_4e2b9b"  # noqa: S105
    path = tmp_path / "lifecycle.toml"
    path.write_text(
        "\n".join(
            [
                "version = 1",
                'name = ""',
                f'credential = "https://user:password@example.test/{secret}"',
                'host_path = "/Users/private-host-path"',
                'raw_command = "curl --header secret"',
                'placeholder = "${UNRESOLVED_VALUE}"',
                'control_identifier = "bad\\u001fidentifier"',
                "[processes.app]",
                "command = []",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(path, project_root=tmp_path)

    serialized = "\n".join(f"{issue.path}|{issue.code}|{issue.message}" for issue in exc_info.value.issues)
    for literal in (
        f"https://user:password@example.test/{secret}",
        "/Users/private-host-path",
        "curl --header secret",
        "${UNRESOLVED_VALUE}",
        "bad\x1fidentifier",
        secret,
    ):
        assert literal not in serialized
