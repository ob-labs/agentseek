from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

import agentseek.cli.lifecycle.json_output as json_contract
from agentseek.cli.lifecycle.json_output import CheckResultDTO, DoctorDataDTO, ErrorDTO
from tests.cli_commands.helpers import build_command_app

pytestmark = pytest.mark.usefixtures("create_symlink")


FIXTURES = Path(__file__).parents[1] / "fixtures" / "lifecycle"


class _InfoInternalSecretError(RuntimeError):
    def __str__(self) -> str:
        return "INTERNAL_SECRET at /Users/private/project"


class _DiagnosticInternalSecretError(RuntimeError):
    def __str__(self) -> str:
        return "DIAGNOSTIC_SECRET at /Users/private/project"


class _UnsafeSourceAccessed(AssertionError):
    pass


def _write_v2_project(root: Path) -> None:
    lifecycle_dir = root / ".agentseek"
    lifecycle_dir.mkdir()
    (root / "README.md").write_text("# JSON project\n", encoding="utf-8")
    (lifecycle_dir / "lifecycle.toml").write_text(
        """\
version = 2
template = "example/json"
name = "JSON Project"
description = "Machine-readable project."
guide = "README.md"

[env.API_KEY]
required = true
description = "API key."
aliases = ["TOKEN"]

[services.app]
name = "Application"
kind = "web"
url = "http://127.0.0.1:8000"
primary = true
description = "Local application."
tech = "FastAPI"

[services.app.links]
docs = "https://example.test/docs"

[processes.app]
command = ["python", "RAW_COMMAND_MUST_NOT_APPEAR"]

[checks.app]
target = "http://127.0.0.1:8000/health"

[tasks.setup]
description = "Prepare the application."
command = ["python", "RAW_TASK_COMMAND_MUST_NOT_APPEAR"]
starts = ["app"]
""",
        encoding="utf-8",
    )


def _write_lifecycle(root: Path, content: str) -> None:
    lifecycle_dir = root / ".agentseek"
    lifecycle_dir.mkdir()
    (lifecycle_dir / "lifecycle.toml").write_text(content, encoding="utf-8")


def _write_unsafe_v1_project(root: Path) -> None:
    _write_lifecycle(root, (FIXTURES / "v1-unsafe-projection.toml").read_text(encoding="utf-8"))
    (root / "safe-path.txt").write_text("safe\n", encoding="utf-8")
    (root / "safe-cwd").mkdir()
    outside = root.parent / f"{root.name}-outside"
    outside.mkdir()
    (root / "symlink-out").symlink_to(outside, target_is_directory=True)


def _write_representative_v1_project(root: Path) -> None:
    _write_lifecycle(
        root,
        """\
version = 1
name = "Legacy Project"

[services.api]
url = "http://user:password@127.0.0.1:8000/private"

[processes.app]
command = ["python", "PROCESS_SECRET_MUST_NOT_APPEAR"]

[checks.probe]
target = "http://127.0.0.1:8000/health?token=QUERY_SECRET_MUST_NOT_APPEAR"

[tasks.setup]
command = ["python", "TASK_SECRET_MUST_NOT_APPEAR"]
""",
    )


def test_public_json_nested_dtos_are_explicit_closed_models() -> None:
    expected_fields = {
        "ProjectFileDTO": ("path", "rel"),
        "ProjectDTO": ("template", "name", "description", "guide"),
        "EnvironmentRequirementDTO": ("name", "required", "description", "aliases"),
        "ProviderDTO": ("type", "id", "process_id", "task_id"),
        "ReferenceDTO": ("rel", "url"),
        "ServiceDTO": (
            "id",
            "name",
            "description",
            "url",
            "kind",
            "display",
            "primary",
            "tech",
            "providers",
            "check_ids",
            "links",
        ),
        "CheckDefinitionDTO": ("id", "service_id", "type", "target", "state"),
        "TaskDTO": ("id", "description", "starts", "stops"),
        "ActionDTO": ("id", "type", "label", "service_id", "url", "reference_rel", "task_id"),
        "EmptyWarningDetailsDTO": (),
        "UnsafeEndpointWarningDetailsDTO": ("owner_type", "owner_id", "field"),
        "UnsafePathWarningDetailsDTO": ("owner_type", "owner_id", "index", "field"),
        "DuplicateRequirementWarningDetailsDTO": ("requirement_type", "first_index", "duplicate_index"),
        "WarningDTO": ("code", "message", "details"),
    }

    for dto_name, fields in expected_fields.items():
        dto_type = getattr(json_contract, dto_name, None)
        assert dto_type is not None, f"{dto_name} must be an explicit public DTO"
        assert tuple(dto_type.model_fields) == fields
        assert dto_type.model_config["extra"] == "forbid"
        assert dto_type.model_config["frozen"] is True
        assert all("Normalized" not in str(field.annotation) for field in dto_type.model_fields.values())

    assert all(
        "Normalized" not in str(field.annotation)
        for dto_type in (json_contract.InfoDataDTO, json_contract.DoctorDataDTO)
        for field in dto_type.model_fields.values()
    )


def test_info_json_emits_exact_representative_v1_contract(tmp_path: Path, monkeypatch) -> None:
    _write_representative_v1_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["info", "--json"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert result.stdout == (
        '{"schema_version":1,"command":"info","ok":true,"lifecycle_version":1,"data":'
        '{"project":{"template":null,"name":"Legacy Project","description":null,"guide":null},'
        '"metadata_complete":false,"environment":[],"services":'
        '[{"id":"api","name":null,"description":null,"url":null,"kind":null,"display":null,'
        '"primary":null,"tech":null,"providers":[],"check_ids":[],"links":[]}],'
        '"checks":[{"id":"probe","service_id":null,"type":"http","target":null,"state":"not_run"}],'
        '"tasks":[{"id":"setup","description":null,"starts":[],"stops":[]}],"actions":[],"warnings":'
        '[{"code":"lifecycle_v1_metadata_incomplete","message":"Lifecycle v1 metadata is incomplete.",'
        '"details":{}},{"code":"unsafe_endpoint_omitted","message":"Unsafe endpoint was omitted.",'
        '"details":{"owner_type":"check","owner_id":"probe","field":"target"}},'
        '{"code":"unsafe_endpoint_omitted","message":"Unsafe endpoint was omitted.",'
        '"details":{"owner_type":"service","owner_id":"api","field":"url"}}]},"error":null}\n'
    )
    assert "PROCESS_SECRET_MUST_NOT_APPEAR" not in result.stdout
    assert "QUERY_SECRET_MUST_NOT_APPEAR" not in result.stdout
    assert "TASK_SECRET_MUST_NOT_APPEAR" not in result.stdout


def test_doctor_json_emits_exact_representative_static_v1_contract(tmp_path: Path, monkeypatch) -> None:
    _write_representative_v1_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert result.stdout == (
        '{"schema_version":1,"command":"doctor","ok":true,"lifecycle_version":1,"data":'
        '{"passed":true,"live_requested":false,"results":'
        '[{"id":"lifecycle:spec","scope":"project","service_id":null,"type":"lifecycle","state":"pass",'
        '"message":"Lifecycle spec is present.","target":".agentseek/lifecycle.toml"},'
        '{"id":"process-cwd:app","scope":"project","service_id":null,"type":"process_cwd","state":"pass",'
        '"message":". is present.","target":"."},'
        '{"id":"service-check:probe","scope":"project","service_id":null,"type":"http","state":"not_run",'
        '"message":"Live check was not requested.","target":null}],"warnings":'
        '[{"code":"lifecycle_v1_metadata_incomplete","message":"Lifecycle v1 metadata is incomplete.",'
        '"details":{}},{"code":"unsafe_endpoint_omitted","message":"Unsafe endpoint was omitted.",'
        '"details":{"owner_type":"check","owner_id":"probe","field":"target"}},'
        '{"code":"unsafe_endpoint_omitted","message":"Unsafe endpoint was omitted.",'
        '"details":{"owner_type":"service","owner_id":"api","field":"url"}}]},"error":null}\n'
    )
    assert "PROCESS_SECRET_MUST_NOT_APPEAR" not in result.stdout
    assert "QUERY_SECRET_MUST_NOT_APPEAR" not in result.stdout
    assert "TASK_SECRET_MUST_NOT_APPEAR" not in result.stdout


def test_info_json_emits_exact_v2_contract(tmp_path: Path, monkeypatch) -> None:
    _write_v2_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["info", "--json"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert result.stdout == (
        '{"schema_version":1,"command":"info","ok":true,"lifecycle_version":2,"data":'
        '{"project":{"template":"example/json","name":"JSON Project","description":"Machine-readable project.",'
        '"guide":{"path":"README.md","rel":"guide"}},"metadata_complete":true,'
        '"environment":[{"name":"API_KEY","required":true,"description":"API key.","aliases":["TOKEN"]}],'
        '"services":[{"id":"app","name":"Application","description":"Local application.",'
        '"url":"http://127.0.0.1:8000","kind":"web","display":"default","primary":true,"tech":"FastAPI",'
        '"providers":[{"type":"dev","id":"process:app","process_id":"app","task_id":null},'
        '{"type":"task","id":"task:setup","process_id":null,"task_id":"setup"}],"check_ids":["app"],'
        '"links":[{"rel":"docs","url":"https://example.test/docs"}]}],'
        '"checks":[{"id":"app","service_id":"app","type":"http",'
        '"target":"http://127.0.0.1:8000/health","state":"not_run"}],'
        '"tasks":[{"id":"setup","description":"Prepare the application.","starts":["app"],"stops":[]}],'
        '"actions":[{"id":"project:start_dev","type":"start_dev","label":"Start development",'
        '"service_id":null,"url":null,"reference_rel":null,"task_id":null},'
        '{"id":"service:app:open","type":"open_url","label":"Open Application","service_id":"app",'
        '"url":"http://127.0.0.1:8000","reference_rel":null,"task_id":null},'
        '{"id":"service:app:reference:docs","type":"open_reference","label":"Open Application docs",'
        '"service_id":"app","url":"https://example.test/docs","reference_rel":"docs","task_id":null},'
        '{"id":"task:setup","type":"run_task","label":"Run task setup","service_id":null,"url":null,'
        '"reference_rel":null,"task_id":"setup"}],"warnings":[]},"error":null}\n'
    )
    payload = json.loads(result.stdout)
    assert "diagnostic_inputs" not in payload["data"]
    assert "RAW_COMMAND_MUST_NOT_APPEAR" not in result.stdout
    assert "RAW_TASK_COMMAND_MUST_NOT_APPEAR" not in result.stdout


def test_info_json_maps_missing_lifecycle_to_one_stdout_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["info", "--json"])

    assert result.exit_code == 2
    assert result.stderr == ""
    assert result.stdout == (
        '{"schema_version":1,"command":"info","ok":false,"lifecycle_version":null,"data":null,'
        '"error":{"code":"lifecycle_not_found","message":"No lifecycle.toml was found.","details":{}}}\n'
    )


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (
            "version = [\n",
            '{"schema_version":1,"command":"info","ok":false,"lifecycle_version":null,"data":null,'
            '"error":{"code":"lifecycle_toml_invalid","message":"The lifecycle TOML is invalid.",'
            '"details":{"line":null,"column":null}}}\n',
        ),
        (
            'version = 3\nname = "Unsupported"\n',
            '{"schema_version":1,"command":"info","ok":false,"lifecycle_version":3,"data":null,'
            '"error":{"code":"lifecycle_version_unsupported","message":"The lifecycle version is unsupported.",'
            '"details":{"found":3,"supported":[1,2]}}}\n',
        ),
        (
            'version = 1\nname = ""\nunexpected = "REJECTED_SECRET"\n[processes.app]\ncommand = []\n',
            '{"schema_version":1,"command":"info","ok":false,"lifecycle_version":1,"data":null,'
            '"error":{"code":"lifecycle_validation_failed","message":"The lifecycle specification is invalid.",'
            '"details":{"issues":[{"path":"processes.app.command","code":"command_empty",'
            '"message":"Command must not be empty."},{"path":"unexpected","code":"field_forbidden",'
            '"message":"Field is not allowed."}]}}}\n',
        ),
    ],
)
def test_info_json_maps_typed_lifecycle_errors(
    tmp_path: Path,
    monkeypatch,
    content: str,
    expected: str,
) -> None:
    _write_lifecycle(tmp_path, content)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["info", "--json"])

    assert result.exit_code == 2
    assert result.stderr == ""
    assert result.stdout == expected
    assert "REJECTED_SECRET" not in result.stdout


def test_info_json_redacts_unexpected_internal_errors(tmp_path: Path, monkeypatch) -> None:
    _write_v2_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fail_normalization(*_args: object, **_kwargs: object) -> None:
        raise _InfoInternalSecretError

    monkeypatch.setattr("agentseek.cli.lifecycle.json_commands.normalize_lifecycle", fail_normalization)

    result = CliRunner().invoke(build_command_app(), ["info", "--json"])

    assert result.exit_code == 1
    assert result.stderr == ""
    assert result.stdout == (
        '{"schema_version":1,"command":"info","ok":false,"lifecycle_version":2,"data":null,'
        '"error":{"code":"internal_error","message":"Unexpected internal error.","details":{}}}\n'
    )
    assert "INTERNAL_SECRET" not in result.stdout
    assert "/Users/private/project" not in result.stdout


def test_info_json_internal_boundary_also_wraps_error_projection(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    def fail_error_projection(*_args: object, **_kwargs: object) -> None:
        raise _InfoInternalSecretError

    monkeypatch.setattr("agentseek.cli.lifecycle.json_commands._lifecycle_error_dto", fail_error_projection)

    result = CliRunner().invoke(build_command_app(), ["info", "--json"])

    assert result.exit_code == 1
    assert result.stderr == ""
    assert result.stdout == (
        '{"schema_version":1,"command":"info","ok":false,"lifecycle_version":null,"data":null,'
        '"error":{"code":"internal_error","message":"Unexpected internal error.","details":{}}}\n'
    )


def test_doctor_json_emits_exact_static_v2_contract(tmp_path: Path, monkeypatch) -> None:
    _write_v2_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("API_KEY", "ENVIRONMENT_SECRET_MUST_NOT_APPEAR")

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert result.stdout == (
        '{"schema_version":1,"command":"doctor","ok":true,"lifecycle_version":2,"data":'
        '{"passed":true,"live_requested":false,"results":'
        '[{"id":"env:API_KEY","scope":"project","service_id":null,"type":"env","state":"pass",'
        '"message":"API_KEY or TOKEN is configured.","target":"API_KEY"},'
        '{"id":"lifecycle:spec","scope":"project","service_id":null,"type":"lifecycle","state":"pass",'
        '"message":"Lifecycle spec is present.","target":".agentseek/lifecycle.toml"},'
        '{"id":"process-cwd:app","scope":"project","service_id":null,"type":"process_cwd","state":"pass",'
        '"message":". is present.","target":"."},'
        '{"id":"service-check:app","scope":"service","service_id":"app","type":"http","state":"not_run",'
        '"message":"Live check was not requested.","target":"http://127.0.0.1:8000/health"}],'
        '"warnings":[]},"error":null}\n'
    )
    assert "ENVIRONMENT_SECRET_MUST_NOT_APPEAR" not in result.stdout


def test_doctor_json_reports_all_static_sources_and_keeps_check_failure_handled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_lifecycle(
        tmp_path,
        """\
version = 2
template = "example/static-failures"
name = "Static Failures"
env_file = ".env"

[tools]
required = ["agentseek-tool-that-does-not-exist"]

[paths]
required = ["required.txt"]

[env.DEFAULTED]
default = "DEFAULT_SECRET_MUST_NOT_APPEAR"

[env.OPTIONAL]
required = false

[env.REQUIRED]
required = true

[processes.app]
command = ["python", "RAW_COMMAND_MUST_NOT_APPEAR"]
cwd = "missing-dir"
""",
    )
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["error"] is None
    assert payload["data"]["passed"] is False
    assert payload["data"]["live_requested"] is False
    results = payload["data"]["results"]
    assert [item["id"] for item in results] == [
        "env-file:.env",
        "env:DEFAULTED",
        "env:OPTIONAL",
        "env:REQUIRED",
        "lifecycle:spec",
        "path:required.txt",
        "process-cwd:app",
        "tool:agentseek-tool-that-does-not-exist",
    ]
    assert {item["id"]: item["state"] for item in results} == {
        "env-file:.env": "fail",
        "env:DEFAULTED": "pass",
        "env:OPTIONAL": "pass",
        "env:REQUIRED": "fail",
        "lifecycle:spec": "pass",
        "path:required.txt": "fail",
        "process-cwd:app": "fail",
        "tool:agentseek-tool-that-does-not-exist": "fail",
    }
    assert {item["id"]: item["target"] for item in results} == {
        "env-file:.env": ".env",
        "env:DEFAULTED": "DEFAULTED",
        "env:OPTIONAL": "OPTIONAL",
        "env:REQUIRED": "REQUIRED",
        "lifecycle:spec": ".agentseek/lifecycle.toml",
        "path:required.txt": "required.txt",
        "process-cwd:app": "missing-dir",
        "tool:agentseek-tool-that-does-not-exist": "agentseek-tool-that-does-not-exist",
    }
    assert "DEFAULT_SECRET_MUST_NOT_APPEAR" not in result.stdout
    assert "RAW_COMMAND_MUST_NOT_APPEAR" not in result.stdout


def test_doctor_live_json_executes_safe_http_checks(tmp_path: Path, monkeypatch) -> None:
    _write_v2_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("API_KEY", "configured")
    requested: list[tuple[str, float]] = []

    class Response:
        status_code = 204

    def get(url: str, *, timeout: float) -> Response:
        requested.append((url, timeout))
        return Response()

    monkeypatch.setattr(httpx, "get", get)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--live", "--json"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["data"]["live_requested"] is True
    assert payload["data"]["passed"] is True
    http_result = next(item for item in payload["data"]["results"] if item["id"] == "service-check:app")
    assert http_result == {
        "id": "service-check:app",
        "scope": "service",
        "service_id": "app",
        "type": "http",
        "state": "pass",
        "message": "http://127.0.0.1:8000/health is reachable.",
        "target": "http://127.0.0.1:8000/health",
    }
    assert requested == [("http://127.0.0.1:8000/health", 2.0)]


def test_doctor_strict_json_is_a_structured_option_conflict(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--strict", "--json"])

    assert result.exit_code == 2
    assert result.stderr == ""
    assert result.stdout == (
        '{"schema_version":1,"command":"doctor","ok":false,"lifecycle_version":null,"data":null,'
        '"error":{"code":"cli_option_conflict","message":"Options --strict and --json cannot be combined.",'
        '"details":{"options":["--json","--strict"]}}}\n'
    )


def test_doctor_json_maps_missing_lifecycle_to_one_stdout_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 2
    assert result.stderr == ""
    assert result.stdout == (
        '{"schema_version":1,"command":"doctor","ok":false,"lifecycle_version":null,"data":null,'
        '"error":{"code":"lifecycle_not_found","message":"No lifecycle.toml was found.","details":{}}}\n'
    )


def test_doctor_json_redacts_unexpected_internal_errors(tmp_path: Path, monkeypatch) -> None:
    _write_v2_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    def fail_diagnostics(*_args: object, **_kwargs: object) -> None:
        raise _DiagnosticInternalSecretError

    monkeypatch.setattr("agentseek.cli.lifecycle.json_commands.evaluate_doctor_json", fail_diagnostics)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 1
    assert result.stderr == ""
    assert result.stdout == (
        '{"schema_version":1,"command":"doctor","ok":false,"lifecycle_version":2,"data":null,'
        '"error":{"code":"internal_error","message":"Unexpected internal error.","details":{}}}\n'
    )
    assert "DIAGNOSTIC_SECRET" not in result.stdout
    assert "/Users/private/project" not in result.stdout


def test_info_json_projects_unsafe_v1_without_leaking_literals(tmp_path: Path, monkeypatch) -> None:
    _write_unsafe_v1_project(tmp_path)
    monkeypatch.chdir(tmp_path)

    first = CliRunner().invoke(build_command_app(), ["info", "--json"])
    second = CliRunner().invoke(build_command_app(), ["info", "--verbose", "--json"])

    assert first.exit_code == second.exit_code == 0
    assert first.stderr == second.stderr == ""
    assert first.stdout == second.stdout
    payload = json.loads(first.stdout)
    assert payload["lifecycle_version"] == 1
    assert payload["data"]["metadata_complete"] is False
    assert payload["data"]["services"][0]["url"] is None
    assert payload["data"]["checks"][0]["target"] is None
    assert payload["data"]["actions"] == []
    assert {warning["code"] for warning in payload["data"]["warnings"]} == {
        "duplicate_requirement_collapsed",
        "lifecycle_v1_metadata_incomplete",
        "unsafe_endpoint_omitted",
        "unsafe_path_omitted",
    }
    for forbidden in (
        "service-user",
        "service-password",
        "query-secret",
        "env-file-secret",
        "unsafe-tool-secret",
        "unsafe-path-secret",
        "escaped-path-secret",
        "process-cwd-secret",
        "task-cwd-secret",
        "process-command-secret",
        "task-command-secret",
        "environment-default-secret",
        str(tmp_path.resolve()),
    ):
        assert forbidden not in first.stdout


def test_doctor_live_json_never_accesses_unsafe_v1_sources(tmp_path: Path, monkeypatch) -> None:  # noqa: C901
    _write_unsafe_v1_project(tmp_path)
    monkeypatch.chdir(tmp_path)
    original_exists = Path.exists
    original_is_file = Path.is_file
    original_is_dir = Path.is_dir
    original_open = Path.open

    def reject_unsafe(path: Path) -> None:
        if any(
            marker in str(path)
            for marker in (
                "env-file-secret",
                "unsafe-path-secret",
                "escaped-path-secret",
                "process-cwd-secret",
            )
        ):
            raise _UnsafeSourceAccessed

    def guarded_exists(path: Path) -> bool:
        reject_unsafe(path)
        return original_exists(path)

    def guarded_is_file(path: Path) -> bool:
        reject_unsafe(path)
        return original_is_file(path)

    def guarded_is_dir(path: Path) -> bool:
        reject_unsafe(path)
        return original_is_dir(path)

    def guarded_open(path: Path, *args: object, **kwargs: object):
        reject_unsafe(path)
        return cast("Any", original_open)(path, *args, **kwargs)

    looked_up: list[str] = []

    def which(tool: str) -> str | None:
        looked_up.append(tool)
        if tool != "python":
            raise _UnsafeSourceAccessed
        return "/safe/python"

    def request(*_args: object, **_kwargs: object) -> None:
        raise _UnsafeSourceAccessed

    monkeypatch.setattr(Path, "exists", guarded_exists)
    monkeypatch.setattr(Path, "is_file", guarded_is_file)
    monkeypatch.setattr(Path, "is_dir", guarded_is_dir)
    monkeypatch.setattr(Path, "open", guarded_open)
    monkeypatch.setattr(shutil, "which", which)
    monkeypatch.setattr(httpx, "get", request)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--live", "--json"])

    assert result.exit_code == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["passed"] is False
    result_items = payload["data"]["results"]
    result_ids = [item["id"] for item in result_items]
    assert len(result_ids) == len(set(result_ids))
    results = {item["id"]: item for item in result_items}
    assert looked_up == ["python"]
    assert results["unsafe-path:env-file"]["message"] == "Unsafe project path was not checked."
    assert results["unsafe-path:required-tool:1"]["message"] == "Unsafe executable requirement was not checked."
    assert results["unsafe-path:required:1"]["message"] == "Unsafe project path was not checked."
    assert results["unsafe-path:required:3"]["message"] == "Unsafe project path was not checked."
    assert results["unsafe-path:process-cwd:0"]["message"] == "Unsafe project path was not checked."
    assert results["service-check:probe"] == {
        "id": "service-check:probe",
        "scope": "project",
        "service_id": None,
        "type": "http",
        "state": "fail",
        "message": "Unsafe endpoint was not checked.",
        "target": None,
    }
    assert "unsafe-path:task" not in results
    assert result_ids.count("tool:python") == 1
    assert result_ids.count("path:safe-path.txt") == 1
    for forbidden in (
        "env-file-secret",
        "unsafe-tool-secret",
        "unsafe-path-secret",
        "escaped-path-secret",
        "process-cwd-secret",
        "query-secret",
        "environment-default-secret",
    ):
        assert forbidden not in result.stdout


def test_doctor_json_checks_declared_names_in_safe_env_file_without_emitting_values(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_lifecycle(
        tmp_path,
        """\
version = 2
template = "example/env-file"
name = "Env File"
env_file = ".env"

[env.API_KEY]
required = true
aliases = ["TOKEN"]

[processes.app]
command = ["python", "app.py"]
""",
    )
    (tmp_path / ".env").write_text(
        "TOKEN=DOTENV_SECRET_MUST_NOT_APPEAR\nUNDECLARED_SECRET=ALSO_MUST_NOT_APPEAR\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("TOKEN", raising=False)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    results = {item["id"]: item for item in payload["data"]["results"]}
    assert results["env-file:.env"]["state"] == "pass"
    assert results["env:API_KEY"]["state"] == "pass"
    assert results["env:API_KEY"]["message"] == "API_KEY or TOKEN is configured."
    assert "DOTENV_SECRET_MUST_NOT_APPEAR" not in result.stdout
    assert "UNDECLARED_SECRET" not in result.stdout
    assert "ALSO_MUST_NOT_APPEAR" not in result.stdout


def test_doctor_json_uses_nonempty_alias_when_primary_environment_value_is_empty(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_v2_project(tmp_path)
    monkeypatch.setenv("API_KEY", "")
    monkeypatch.setenv("TOKEN", "ALIAS_SECRET_MUST_NOT_APPEAR")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    check = next(item for item in payload["data"]["results"] if item["id"] == "env:API_KEY")
    assert check["state"] == "pass"
    assert "ALIAS_SECRET_MUST_NOT_APPEAR" not in result.stdout


def test_doctor_json_uses_env_file_when_same_shell_key_is_empty(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle(
        tmp_path,
        """\
version = 2
template = "example/env-file"
name = "Env File"
env_file = ".env"

[env.API_KEY]
required = true

[processes.app]
command = ["python", "app.py"]
""",
    )
    (tmp_path / ".env").write_text("API_KEY=DOTENV_SECRET_MUST_NOT_APPEAR\n", encoding="utf-8")
    monkeypatch.setenv("API_KEY", "")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    check = next(item for item in payload["data"]["results"] if item["id"] == "env:API_KEY")
    assert check["state"] == "pass"
    assert "DOTENV_SECRET_MUST_NOT_APPEAR" not in result.stdout


def test_doctor_json_keeps_env_parser_diagnostics_out_of_stderr(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle(
        tmp_path,
        """\
version = 2
template = "example/malformed-env-file"
name = "Malformed Env File"
env_file = ".env"

[env.API_KEY]
required = true

[processes.app]
command = ["python", "app.py"]
""",
    )
    (tmp_path / ".env").write_text("this is not a dotenv assignment\n", encoding="utf-8")
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["passed"] is False


@pytest.mark.parametrize(
    ("content", "lifecycle_version", "code", "details"),
    [
        (
            "version = [\n",
            None,
            "lifecycle_toml_invalid",
            {"line": None, "column": None},
        ),
        (
            "version = 3\n",
            3,
            "lifecycle_version_unsupported",
            {"found": 3, "supported": [1, 2]},
        ),
        (
            'version = 1\nname = ""\n[processes.app]\ncommand = []\n',
            1,
            "lifecycle_validation_failed",
            {
                "issues": [
                    {
                        "path": "processes.app.command",
                        "code": "command_empty",
                        "message": "Command must not be empty.",
                    }
                ]
            },
        ),
    ],
)
def test_doctor_json_maps_typed_lifecycle_errors(
    tmp_path: Path,
    monkeypatch,
    content: str,
    lifecycle_version: int | None,
    code: str,
    details: dict[str, object],
) -> None:
    _write_lifecycle(tmp_path, content)
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 2
    assert result.stderr == ""
    assert result.stdout.endswith("\n") and result.stdout.count("\n") == 1
    payload = json.loads(result.stdout)
    assert payload["command"] == "doctor"
    assert payload["ok"] is False
    assert payload["lifecycle_version"] == lifecycle_version
    assert payload["data"] is None
    assert payload["error"]["code"] == code
    assert payload["error"]["details"] == details


def test_doctor_json_does_not_treat_projection_warnings_as_readiness_failures(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_lifecycle(
        tmp_path,
        'version = 1\nname = "Legacy Project"\n[processes.app]\ncommand = ["python", "app.py"]\n',
    )
    monkeypatch.chdir(tmp_path)

    first = CliRunner().invoke(build_command_app(), ["doctor", "--json"])
    second = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert first.exit_code == second.exit_code == 0
    assert first.stderr == second.stderr == ""
    assert first.stdout == second.stdout
    payload = json.loads(first.stdout)
    assert payload["data"]["passed"] is True
    assert [warning["code"] for warning in payload["data"]["warnings"]] == ["lifecycle_v1_metadata_incomplete"]


def test_doctor_live_json_retries_and_reports_http_failure_as_handled_result(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_v2_project(tmp_path)
    lifecycle_path = tmp_path / ".agentseek" / "lifecycle.toml"
    lifecycle_path.write_text(
        lifecycle_path.read_text(encoding="utf-8").replace(
            '[checks.app]\ntarget = "http://127.0.0.1:8000/health"',
            '[checks.app]\ntarget = "http://127.0.0.1:8000/health"\nattempts = 2',
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("API_KEY", "configured")
    requested: list[str] = []

    class Response:
        status_code = 503

    def get(url: str, *, timeout: float) -> Response:
        del timeout
        requested.append(url)
        return Response()

    monkeypatch.setattr(httpx, "get", get)
    monkeypatch.setattr("agentseek.cli.lifecycle.diagnostics.time.sleep", lambda _seconds: None)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--live", "--json"])

    assert result.exit_code == 1
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["error"] is None
    assert payload["data"]["passed"] is False
    check = next(item for item in payload["data"]["results"] if item["id"] == "service-check:app")
    assert check["state"] == "fail"
    assert check["message"] == "http://127.0.0.1:8000/health is not reachable."
    assert requested == ["http://127.0.0.1:8000/health", "http://127.0.0.1:8000/health"]


@pytest.mark.parametrize(
    "error",
    [ValueError("invalid timeout"), OverflowError("timestamp out of range")],
    ids=["invalid-value", "platform-overflow"],
)
def test_doctor_live_json_handles_legacy_http_runtime_error_as_failed_check(
    tmp_path: Path,
    monkeypatch,
    error: Exception,
) -> None:
    _write_lifecycle(
        tmp_path,
        """\
version = 1
name = "Legacy Invalid Timeout"

[processes.app]
command = ["python", "app.py"]

[checks.app]
target = "http://127.0.0.1:8000/health"
timeout = -1.0
""",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(httpx, "get", lambda *_args, **_kwargs: (_ for _ in ()).throw(error))

    result = CliRunner().invoke(build_command_app(), ["doctor", "--live", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["error"] is None
    check = next(item for item in payload["data"]["results"] if item["id"] == "service-check:app")
    assert check["state"] == "fail"


def test_doctor_json_keeps_unsafe_v1_http_not_run_until_live_is_requested(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _write_lifecycle(
        tmp_path,
        """\
version = 1
name = "Unsafe Legacy Check"

[processes.app]
command = ["python", "app.py"]

[checks.probe]
target = "http://127.0.0.1:8000/health?SECRET_QUERY=yes"
""",
    )
    monkeypatch.chdir(tmp_path)

    def request(*_args: object, **_kwargs: object) -> None:
        raise _UnsafeSourceAccessed

    monkeypatch.setattr(httpx, "get", request)

    static = CliRunner().invoke(build_command_app(), ["doctor", "--json"])
    live = CliRunner().invoke(build_command_app(), ["doctor", "--live", "--json"])

    assert static.exit_code == 0
    assert live.exit_code == 1
    static_payload = json.loads(static.stdout)
    live_payload = json.loads(live.stdout)
    static_result = next(item for item in static_payload["data"]["results"] if item["id"] == "service-check:probe")
    live_result = next(item for item in live_payload["data"]["results"] if item["id"] == "service-check:probe")
    assert static_payload["data"]["passed"] is True
    assert static_result["state"] == "not_run"
    assert static_result["target"] is None
    assert live_payload["ok"] is True
    assert live_payload["data"]["passed"] is False
    assert live_result["state"] == "fail"
    assert live_result["message"] == "Unsafe endpoint was not checked."
    assert live_result["target"] is None
    assert "SECRET_QUERY" not in static.stdout + live.stdout


def test_doctor_json_preserves_valid_v1_empty_identifiers(tmp_path: Path, monkeypatch) -> None:
    _write_lifecycle(
        tmp_path,
        """\
version = 1
name = "Legacy Empty IDs"

[env.""]
aliases = ["", ""]

[services.""]
url = "http://127.0.0.1:8000"

[processes.""]
command = ["python", "app.py"]

[checks.""]
target = "http://127.0.0.1:8000/health"
""",
    )
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["doctor", "--json"])

    assert result.exit_code == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["data"]["passed"] is True
    assert [item["id"] for item in payload["data"]["results"]] == [
        "env:",
        "lifecycle:spec",
        "process-cwd:",
        "service-check:",
    ]
    assert payload["data"]["results"][-1]["scope"] == "project"


def test_info_json_uses_normative_utf8_and_control_character_escaping(tmp_path: Path, monkeypatch) -> None:
    _write_v2_project(tmp_path)
    lifecycle_path = tmp_path / ".agentseek" / "lifecycle.toml"
    lifecycle_path.write_text(
        lifecycle_path.read_text(encoding="utf-8").replace(
            'name = "JSON Project"',
            'name = "Café \\"quoted\\" / slash \\t tab \\u001F"',
        ),
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(build_command_app(), ["info", "--json"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Café" in result.stdout
    assert "Caf\\u00e9" not in result.stdout
    assert "\\t" in result.stdout
    assert "\\u001f" in result.stdout
    assert "\\/" not in result.stdout
    assert json.loads(result.stdout)["data"]["project"]["name"] == 'Café "quoted" / slash \t tab \x1f'


@pytest.mark.parametrize(
    "payload",
    [
        {"code": "unknown", "message": "Unexpected internal error.", "details": {}},
        {"code": "internal_error", "message": "raw exception", "details": {}},
        {
            "code": "lifecycle_not_found",
            "message": "No lifecycle.toml was found.",
            "details": {"line": 1},
        },
        {
            "code": "cli_option_conflict",
            "message": "Options --strict and --json cannot be combined.",
            "details": {"options": ["--strict", "--json"]},
        },
    ],
)
def test_error_dto_rejects_noncanonical_code_message_or_details(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ErrorDTO.model_validate(payload)


@pytest.mark.parametrize(
    ("scope", "service_id"),
    [("project", "app"), ("service", None)],
)
def test_check_result_dto_rejects_inconsistent_scope(scope: str, service_id: str | None) -> None:
    with pytest.raises(ValidationError):
        CheckResultDTO.model_validate({
            "id": "service-check:app",
            "scope": scope,
            "service_id": service_id,
            "type": "http",
            "state": "not_run",
            "message": "Live check was not requested.",
            "target": "http://127.0.0.1:8000/health",
        })


@pytest.mark.parametrize(
    ("passed", "results"),
    [
        (
            True,
            [
                {
                    "id": "path:missing",
                    "scope": "project",
                    "service_id": None,
                    "type": "path",
                    "state": "fail",
                    "message": "missing is missing.",
                    "target": "missing",
                }
            ],
        ),
        (
            False,
            [
                {
                    "id": "service-check:app",
                    "scope": "service",
                    "service_id": "app",
                    "type": "http",
                    "state": "not_run",
                    "message": "Live check was not requested.",
                    "target": "http://127.0.0.1:8000/health",
                }
            ],
        ),
        (
            True,
            [
                {
                    "id": "tool:zsh",
                    "scope": "project",
                    "service_id": None,
                    "type": "tool",
                    "state": "pass",
                    "message": "zsh is available.",
                    "target": "zsh",
                },
                {
                    "id": "lifecycle:spec",
                    "scope": "project",
                    "service_id": None,
                    "type": "lifecycle",
                    "state": "pass",
                    "message": "Lifecycle spec is present.",
                    "target": ".agentseek/lifecycle.toml",
                },
            ],
        ),
    ],
)
def test_doctor_data_dto_rejects_inconsistent_passed_or_noncanonical_results(
    passed: bool,
    results: list[dict[str, object]],
) -> None:
    with pytest.raises(ValidationError):
        DoctorDataDTO.model_validate({
            "passed": passed,
            "live_requested": False,
            "results": results,
            "warnings": [],
        })
