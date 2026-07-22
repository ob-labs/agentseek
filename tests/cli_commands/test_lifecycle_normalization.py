from __future__ import annotations

import copy
import json
import pickle
import shutil
import socket
import subprocess
import tomllib
import urllib.request
from collections import UserDict
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

import pytest
from pydantic import PrivateAttr, ValidationError

from agentseek.cli.lifecycle.authored import LifecycleSpecV1, LifecycleSpecV2
from agentseek.cli.lifecycle.discovery import (
    DiagnosticInputs,
    EnvironmentDiagnosticSource,
    HttpDiagnosticSource,
    NormalizationWarning,
    NormalizedAction,
    NormalizedCheckDefinition,
    NormalizedEnvironmentRequirement,
    NormalizedLifecycleProject,
    NormalizedProject,
    NormalizedProjectFile,
    NormalizedProvider,
    NormalizedReference,
    NormalizedService,
    NormalizedTask,
    PathDiagnosticSource,
    SafeExecutableName,
    SafeModel,
    SafeProjectPath,
    ToolDiagnosticSource,
    WarningCode,
)
from agentseek.cli.lifecycle.normalize import normalize_lifecycle
from agentseek.cli.lifecycle.safety import UnsafeProjectPathError

FIXTURES = Path(__file__).parent.parent / "fixtures" / "lifecycle"


class _ExternalStateAccessed(AssertionError):
    pass


def _normalized_v2_projection_fixture(project_root: Path) -> LifecycleSpecV2:
    return LifecycleSpecV2.model_validate(
        tomllib.loads((FIXTURES / "v2-normalization-projection.toml").read_text(encoding="utf-8")),
        context={
            "project_root": project_root,
            "loader_path": project_root / ".agentseek" / "loader-path-sentinel.toml",
        },
    )


def _v2_topology_spec(project_root: Path, *, reverse: bool = False) -> LifecycleSpecV2:
    """Build equivalent v2 topology inputs with deliberately varied ordering."""
    services: list[tuple[str, dict[str, object]]] = [
        (
            "app",
            {
                "name": "Application",
                "url": "http://127.0.0.1:8000",
                "kind": "web",
                "primary": True,
                "description": "Browser application.",
            },
        ),
        (
            "api",
            {
                "name": "API",
                "url": "http://127.0.0.1:8100",
                "kind": "api",
                "display": "advanced",
                "description": "Application API.",
                "links": {
                    "docs": "https://docs.example.test/api",
                    "api_docs": "https://docs.example.test/api/openapi",
                    "studio": "https://studio.example.test/?baseUrl=https%3A%2F%2F127.0.0.1%3A8100",
                },
            },
        ),
        (
            "database",
            {
                "name": "Database",
                "url": "mysql://127.0.0.1:3306/app",
                "kind": "database",
                "description": "Application database.",
            },
        ),
        (
            "other",
            {
                "name": "Other service",
                "url": "http://127.0.0.1:8200",
                "kind": "other",
                "display": "advanced",
                "description": "No endpoint action.",
            },
        ),
        (
            "protocol",
            {
                "name": "Hidden protocol",
                "url": "http://127.0.0.1:8300",
                "kind": "protocol",
                "display": "hidden",
                "description": "Internal protocol service.",
            },
        ),
    ]
    processes: list[tuple[str, dict[str, object]]] = [
        ("alpha", {"command": ["python", "alpha.py"], "provides": ["app", "app", "api"]}),
        ("bravo", {"command": ["python", "bravo.py"], "provides": ["app"]}),
        ("hidden", {"command": ["python", "hidden.py"], "provides": ["protocol", "protocol"]}),
    ]
    checks: list[tuple[str, dict[str, object]]] = [
        ("app", {"target": "http://127.0.0.1:8000/health"}),
        ("api-probe", {"target": "http://127.0.0.1:8100/health", "service": "api"}),
    ]
    tasks: list[tuple[str, dict[str, object]]] = [
        (
            "multi",
            {
                "command": ["python", "multi.py"],
                "starts": ["app", "app", "api"],
                "stops": ["database", "database"],
            },
        ),
        (
            "hidden-only",
            {
                "command": ["python", "hidden.py"],
                "starts": ["protocol", "protocol"],
                "stops": ["protocol"],
            },
        ),
    ]
    if reverse:
        services.reverse()
        processes.reverse()
        checks.reverse()
        tasks.reverse()
        for _, process in processes:
            provides = process["provides"]
            assert isinstance(provides, list)
            process["provides"] = list(reversed(provides))
        for _, task in tasks:
            for effect in ("starts", "stops"):
                if effect in task:
                    service_ids = task[effect]
                    assert isinstance(service_ids, list)
                    task[effect] = list(reversed(service_ids))
        api_service = dict(services)["api"]
        links = api_service["links"]
        assert isinstance(links, dict)
        api_service["links"] = dict(reversed(tuple(links.items())))
    return LifecycleSpecV2.model_validate(
        {
            "version": 2,
            "template": "example/topology",
            "name": "Topology Project",
            "services": dict(services),
            "processes": dict(processes),
            "checks": dict(checks),
            "tasks": dict(tasks),
        },
        context={
            "project_root": project_root,
            "loader_path": project_root / ".agentseek" / "loader-path-sentinel.toml",
        },
    )


@pytest.mark.parametrize(
    ("model", "fields"),
    [
        (SafeModel, ()),
        (NormalizedProjectFile, ("path", "rel")),
        (NormalizedProject, ("template", "name", "description", "guide")),
        (NormalizedEnvironmentRequirement, ("name", "required", "description", "aliases")),
        (NormalizedProvider, ("type", "id", "process_id", "task_id")),
        (NormalizedReference, ("rel", "url")),
        (
            NormalizedService,
            (
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
        ),
        (NormalizedCheckDefinition, ("id", "service_id", "type", "target", "state")),
        (NormalizedTask, ("id", "description", "starts", "stops")),
        (NormalizedAction, ("id", "type", "label", "service_id", "url", "reference_rel", "task_id")),
        (NormalizationWarning, ("code", "message", "details")),
        (SafeProjectPath, ("path",)),
        (SafeExecutableName, ("name",)),
        (PathDiagnosticSource, ("id", "owner_id", "source_index", "path")),
        (ToolDiagnosticSource, ("id", "source_index", "tool")),
        (EnvironmentDiagnosticSource, ("id", "name", "aliases", "required", "has_usable_default")),
        (HttpDiagnosticSource, ("id", "service_id", "target", "timeout", "attempts")),
        (
            DiagnosticInputs,
            (
                "env_file",
                "tools",
                "required_paths",
                "process_cwds",
                "unsafe_task_cwd_ids",
                "environment",
                "http_checks",
            ),
        ),
        (
            NormalizedLifecycleProject,
            (
                "lifecycle_version",
                "project",
                "metadata_complete",
                "environment",
                "services",
                "checks",
                "tasks",
                "actions",
                "warnings",
                "diagnostic_inputs",
            ),
        ),
    ],
)
def test_model_shape_field_order_and_configuration(model: type[SafeModel], fields: tuple[str, ...]) -> None:
    assert tuple(model.model_fields) == fields
    assert model.model_config["extra"] == "forbid"
    assert model.model_config["frozen"] is True


def test_model_shape_defaults_are_immutable_tuples_and_factory_created() -> None:
    process_cwds = (PathDiagnosticSource(id="process-cwd:app", owner_id="app", path=SafeProjectPath(path=".")),)
    project = NormalizedLifecycleProject(
        lifecycle_version=2,
        project=NormalizedProject(template="example/default", name="Example", description=None, guide=None),
        metadata_complete=True,
        diagnostic_inputs=DiagnosticInputs(process_cwds=process_cwds),
    )
    default_inputs = DiagnosticInputs()

    assert project.environment == ()
    assert project.services == ()
    assert project.checks == ()
    assert project.tasks == ()
    assert project.actions == ()
    assert project.warnings == ()
    assert project.diagnostic_inputs.process_cwds == process_cwds
    assert default_inputs.env_file is None
    assert default_inputs.tools == ()
    assert default_inputs.required_paths == ()
    assert default_inputs.process_cwds == ()
    assert default_inputs.unsafe_task_cwd_ids == ()
    assert default_inputs.environment == ()
    assert default_inputs.http_checks == ()
    assert NormalizedEnvironmentRequirement(name="TOKEN", required=True, description=None).aliases == ()
    assert (
        NormalizedService(
            id="web", name=None, description=None, url=None, kind=None, display=None, primary=None, tech=None
        ).providers
        == ()
    )
    assert NormalizedTask(id="start", description=None).starts == ()


@pytest.mark.parametrize(
    "provider",
    [
        {"type": "dev", "id": "process:app", "process_id": "app"},
        {"type": "task", "id": "task:stack", "task_id": "stack"},
    ],
)
def test_model_shape_provider_accepts_exact_relationship(provider: dict[str, str]) -> None:
    assert NormalizedProvider.model_validate(provider).model_dump(exclude_none=True) == provider


@pytest.mark.parametrize(
    "provider",
    [
        {"type": "dev", "id": "process:app"},
        {"type": "dev", "id": "process:app", "process_id": "app", "task_id": "stack"},
        {"type": "dev", "id": "process:other", "process_id": "app"},
        {"type": "task", "id": "task:stack"},
        {"type": "task", "id": "task:stack", "task_id": "stack", "process_id": "app"},
        {"type": "task", "id": "task:other", "task_id": "stack"},
    ],
)
def test_model_shape_provider_rejects_noncanonical_relationship(provider: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        NormalizedProvider.model_validate(provider)


@pytest.mark.parametrize(
    "action",
    [
        {"id": "service:web:open", "type": "open_url", "label": "Open", "service_id": "web", "url": "http://127.0.0.1"},
        {
            "id": "service:web:copy",
            "type": "copy_endpoint",
            "label": "Copy",
            "service_id": "web",
            "url": "http://127.0.0.1",
        },
        {
            "id": "service:web:reference:docs",
            "type": "open_reference",
            "label": "Docs",
            "service_id": "web",
            "url": "https://example.test/docs",
            "reference_rel": "docs",
        },
        {"id": "project:start_dev", "type": "start_dev", "label": "Start"},
        {"id": "task:stack", "type": "run_task", "label": "Run", "task_id": "stack"},
    ],
)
def test_model_shape_action_accepts_exact_relationship(action: dict[str, str]) -> None:
    assert NormalizedAction.model_validate(action).model_dump(exclude_none=True) == action


@pytest.mark.parametrize(
    "action",
    [
        {"id": "service:web:copy", "type": "open_url", "label": "Open", "service_id": "web", "url": "http://127.0.0.1"},
        {
            "id": "service:web:open",
            "type": "copy_endpoint",
            "label": "Copy",
            "service_id": "web",
            "url": "http://127.0.0.1",
        },
        {
            "id": "service:web:reference:docs",
            "type": "open_reference",
            "label": "Docs",
            "service_id": "web",
            "url": "http://127.0.0.1",
        },
        {"id": "project:start_dev", "type": "start_dev", "label": "Start", "task_id": "stack"},
        {"id": "task:stack", "type": "run_task", "label": "Run"},
    ],
)
def test_model_shape_action_rejects_noncanonical_relationship(action: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        NormalizedAction.model_validate(action)


def test_model_shape_http_diagnostic_id_is_canonical() -> None:
    source = HttpDiagnosticSource(
        id="service-check:api", service_id="api", target="http://127.0.0.1", timeout=1.0, attempts=1
    )

    assert source.id == "service-check:api"
    with pytest.raises(ValidationError):
        HttpDiagnosticSource(id="api", service_id="api", target="http://127.0.0.1", timeout=1.0, attempts=1)
    with pytest.raises(ValidationError):
        HttpDiagnosticSource(id="service-check:", service_id="api", target="http://127.0.0.1", timeout=1.0, attempts=1)

    legacy = HttpDiagnosticSource(
        id="service-check:", service_id=None, target="http://127.0.0.1", timeout=1.0, attempts=1
    )
    assert legacy.id == "service-check:"


@pytest.mark.parametrize(
    ("code", "details", "message"),
    [
        ("lifecycle_v1_metadata_incomplete", {}, "Lifecycle v1 metadata is incomplete."),
        (
            "unsafe_endpoint_omitted",
            {"owner_type": "service", "owner_id": "app", "field": "url"},
            "Unsafe endpoint was omitted.",
        ),
        (
            "unsafe_path_omitted",
            {"owner_type": "process", "owner_id": "app", "index": None, "field": "cwd"},
            "Unsafe project path was omitted.",
        ),
        (
            "duplicate_requirement_collapsed",
            {"requirement_type": "tool", "first_index": 0, "duplicate_index": 1},
            "Duplicate requirement was collapsed.",
        ),
    ],
)
def test_model_shape_warning_has_fixed_message_and_copied_ordered_details(
    code: WarningCode, details: dict[str, str | int | None], message: str
) -> None:
    warning = NormalizationWarning(code=code, message=message, details=details)
    details["changed"] = "after validation"

    assert warning.message == message
    expected_keys = {
        "lifecycle_v1_metadata_incomplete": (),
        "unsafe_endpoint_omitted": ("owner_type", "owner_id", "field"),
        "unsafe_path_omitted": ("owner_type", "owner_id", "index", "field"),
        "duplicate_requirement_collapsed": ("requirement_type", "first_index", "duplicate_index"),
    }
    assert tuple(warning.details) == expected_keys[code]
    assert type(warning.details) is MappingProxyType
    assert not isinstance(warning.details, dict)
    assert "changed" not in warning.details
    assert warning.details == {key: warning.details[key] for key in expected_keys[code]}
    copied_details = warning.details.copy()
    assert type(copied_details) is dict
    copied_details["changed"] = "copy only"
    assert "changed" not in warning.details
    dumped_details = warning.model_dump()["details"]
    assert type(dumped_details) is dict
    assert tuple(dumped_details) == expected_keys[code]
    assert tuple(json.loads(warning.model_dump_json())["details"]) == expected_keys[code]


@pytest.mark.parametrize(
    "method",
    ["setitem", "delitem", "ior"],
)
def test_model_shape_warning_details_reject_ordinary_mutation_paths(method: str) -> None:
    warning = NormalizationWarning(
        code="unsafe_endpoint_omitted",
        message="Unsafe endpoint was omitted.",
        details={"owner_type": "service", "owner_id": "app", "field": "url"},
    )
    details = warning.details

    with pytest.raises(TypeError):
        if method == "setitem":
            details["owner_id"] = "changed"  # ty: ignore[invalid-assignment]
        elif method == "delitem":
            del details["owner_id"]  # ty: ignore[not-subscriptable]
        else:
            details |= {"owner_id": "changed"}  # ty: ignore[unsupported-operator]

    assert details == {"owner_type": "service", "owner_id": "app", "field": "url"}


@pytest.mark.parametrize("method", ["clear", "pop", "popitem", "setdefault", "update"])
def test_model_shape_warning_details_do_not_expose_mutating_dict_methods(method: str) -> None:
    details = NormalizationWarning(
        code="unsafe_endpoint_omitted",
        message="Unsafe endpoint was omitted.",
        details={"owner_type": "service", "owner_id": "app", "field": "url"},
    ).details

    with pytest.raises(AttributeError):
        getattr(details, method)


@pytest.mark.parametrize("method", ["setitem", "update", "delitem", "clear"])
def test_model_shape_warning_details_reject_dict_base_class_mutation_bypasses(method: str) -> None:
    details = NormalizationWarning(
        code="unsafe_endpoint_omitted",
        message="Unsafe endpoint was omitted.",
        details={"owner_type": "service", "owner_id": "app", "field": "url"},
    ).details

    with pytest.raises(TypeError):
        if method == "setitem":
            dict.__setitem__(details, "owner_id", "changed")  # ty: ignore[invalid-argument-type]
        elif method == "update":
            replacement: dict[str, str | int | None] = {"owner_id": "changed"}
            dict.update(details, replacement)  # ty: ignore[no-matching-overload]
        elif method == "delitem":
            dict.__delitem__(details, "owner_id")  # ty: ignore[invalid-argument-type]
        else:
            dict.clear(details)  # ty: ignore[invalid-argument-type]

    assert details == {"owner_type": "service", "owner_id": "app", "field": "url"}


@pytest.mark.parametrize(
    ("code", "message", "details"),
    [
        (
            "unsafe_path_omitted",
            "Unsafe project path was omitted.",
            MappingProxyType({"owner_type": "required_tool", "owner_id": None, "index": True, "field": "tool"}),
        ),
        (
            "duplicate_requirement_collapsed",
            "Duplicate requirement was collapsed.",
            UserDict({"requirement_type": "path", "first_index": 0.0, "duplicate_index": 1}),
        ),
    ],
)
def test_model_shape_warning_rejects_mapping_wrapped_bool_and_float_indices(
    code: WarningCode,
    message: str,
    details: Mapping[str, object],
) -> None:
    with pytest.raises(ValidationError):
        NormalizationWarning.model_validate({"code": code, "message": message, "details": details})


@pytest.mark.parametrize(
    ("code", "details", "message"),
    [
        ("lifecycle_v1_metadata_incomplete", {}, "Lifecycle v1 metadata is incomplete."),
        (
            "unsafe_endpoint_omitted",
            {"owner_type": "service", "owner_id": "", "field": "url"},
            "Unsafe endpoint was omitted.",
        ),
        (
            "unsafe_endpoint_omitted",
            {"owner_type": "check", "owner_id": "", "field": "target"},
            "Unsafe endpoint was omitted.",
        ),
        (
            "unsafe_path_omitted",
            {"owner_type": "env_file", "owner_id": None, "index": None, "field": "env_file"},
            "Unsafe project path was omitted.",
        ),
        (
            "unsafe_path_omitted",
            {"owner_type": "required_path", "owner_id": None, "index": 0, "field": "path"},
            "Unsafe project path was omitted.",
        ),
        (
            "unsafe_path_omitted",
            {"owner_type": "required_tool", "owner_id": None, "index": 1, "field": "tool"},
            "Unsafe project path was omitted.",
        ),
        (
            "unsafe_path_omitted",
            {"owner_type": "process", "owner_id": "", "index": None, "field": "cwd"},
            "Unsafe project path was omitted.",
        ),
        (
            "unsafe_path_omitted",
            {"owner_type": "task", "owner_id": "", "index": None, "field": "cwd"},
            "Unsafe project path was omitted.",
        ),
        (
            "duplicate_requirement_collapsed",
            {"requirement_type": "path", "first_index": 0, "duplicate_index": 2},
            "Duplicate requirement was collapsed.",
        ),
    ],
)
def test_model_shape_warning_accepts_exact_domain_contract(
    code: WarningCode, details: dict[str, str | int | None], message: str
) -> None:
    assert NormalizationWarning(code=code, message=message, details=details).details == details


@pytest.mark.parametrize(
    ("code", "message", "details"),
    [
        (
            "unsafe_endpoint_omitted",
            "Unsafe endpoint was omitted.",
            {"owner_type": "service", "owner_id": "app", "field": "target"},
        ),
        (
            "unsafe_endpoint_omitted",
            "Unsafe endpoint was omitted.",
            {"owner_type": "check", "owner_id": None, "field": "target"},
        ),
        (
            "unsafe_path_omitted",
            "Unsafe project path was omitted.",
            {"owner_type": "env_file", "owner_id": "env", "index": None, "field": "env_file"},
        ),
        (
            "unsafe_path_omitted",
            "Unsafe project path was omitted.",
            {"owner_type": "required_path", "owner_id": None, "index": -1, "field": "path"},
        ),
        (
            "unsafe_path_omitted",
            "Unsafe project path was omitted.",
            {"owner_type": "required_tool", "owner_id": None, "index": True, "field": "tool"},
        ),
        (
            "unsafe_path_omitted",
            "Unsafe project path was omitted.",
            {"owner_type": "process", "owner_id": "app", "index": 0, "field": "cwd"},
        ),
        (
            "unsafe_path_omitted",
            "Unsafe project path was omitted.",
            {"owner_type": "task", "owner_id": "task", "index": None, "field": "path"},
        ),
        (
            "duplicate_requirement_collapsed",
            "Duplicate requirement was collapsed.",
            {"requirement_type": "service", "first_index": 0, "duplicate_index": 1},
        ),
        (
            "duplicate_requirement_collapsed",
            "Duplicate requirement was collapsed.",
            {"requirement_type": "tool", "first_index": 1, "duplicate_index": 1},
        ),
        (
            "duplicate_requirement_collapsed",
            "Duplicate requirement was collapsed.",
            {"requirement_type": "path", "first_index": 2, "duplicate_index": 1},
        ),
    ],
)
def test_model_shape_warning_rejects_invalid_domain_values(
    code: WarningCode, message: str, details: dict[str, str | int | bool | None]
) -> None:
    with pytest.raises(ValidationError):
        NormalizationWarning.model_validate({"code": code, "message": message, "details": details})


@pytest.mark.parametrize(
    ("code", "message", "details"),
    [
        ("lifecycle_v1_metadata_incomplete", "wrong", {}),
        (
            "unsafe_endpoint_omitted",
            "Unsafe endpoint was omitted.",
            {"owner_id": "app", "owner_type": "service", "field": "url"},
        ),
        (
            "unsafe_path_omitted",
            "Unsafe project path was omitted.",
            {"owner_type": "process", "owner_id": "app", "field": "cwd"},
        ),
        (
            "duplicate_requirement_collapsed",
            "Duplicate requirement was collapsed.",
            {"requirement_type": "tool", "first_index": 0, "duplicate_index": 1, "extra": None},
        ),
    ],
)
def test_model_shape_warning_rejects_noncanonical_message_or_details(
    code: WarningCode, message: str, details: dict[str, str | int | None]
) -> None:
    with pytest.raises(ValidationError):
        NormalizationWarning(code=code, message=message, details=details)


@pytest.mark.parametrize(
    "model_and_data",
    [
        (NormalizedProjectFile, {"path": "README.md", "extra": "no"}),
        (SafeProjectPath, {"path": "README.md", "extra": "no"}),
        (SafeExecutableName, {"name": "python", "extra": "no"}),
    ],
)
def test_model_shape_rejects_unexpected_fields(model_and_data: tuple[type[SafeModel], Mapping[str, object]]) -> None:
    model, data = model_and_data
    with pytest.raises(ValidationError):
        model.model_validate(data)


def test_normalize_lifecycle_minimal_valid_v1_is_conservative_and_redacts_command(tmp_path: Path) -> None:
    spec = LifecycleSpecV1.model_validate({
        "path": tmp_path / ".agentseek" / "lifecycle.toml",
        "version": 1,
        "name": "Example",
        "processes": {"app": {"command": ["python", "never-retain-this-command"]}},
    })

    normalized = normalize_lifecycle(spec, project_root=tmp_path)

    assert normalized.lifecycle_version == 1
    assert normalized.project == NormalizedProject(template=None, name="Example", description=None, guide=None)
    assert normalized.metadata_complete is False
    assert normalized.environment == ()
    assert normalized.services == ()
    assert normalized.checks == ()
    assert normalized.tasks == ()
    assert normalized.actions == ()
    assert normalized.warnings == (
        NormalizationWarning(
            code="lifecycle_v1_metadata_incomplete",
            message="Lifecycle v1 metadata is incomplete.",
            details={},
        ),
    )
    assert normalized.diagnostic_inputs.process_cwds == (
        PathDiagnosticSource(
            id="process-cwd:app",
            owner_id="app",
            path=SafeProjectPath(path="."),
        ),
    )
    assert "never-retain-this-command" not in normalized.model_dump_json()


def test_normalize_lifecycle_valid_v1_empty_identifiers_preserve_authored_identity(tmp_path: Path) -> None:
    authored = tomllib.loads(
        """\
version = 1
name = "Legacy blank IDs"

[env.""]
aliases = ["", ""]

[services.""]
url = "http://127.0.0.1:8000"

[processes.""]
command = ["python", "app.py"]

[checks.""]
target = "http://127.0.0.1:8000/health"

[tasks.""]
command = ["python", "task.py"]
"""
    )
    spec = LifecycleSpecV1.model_validate({**authored, "path": tmp_path / ".agentseek" / "lifecycle.toml"})

    normalized = normalize_lifecycle(spec, project_root=tmp_path)

    assert tuple(requirement.name for requirement in normalized.environment) == ("",)
    assert normalized.environment[0].aliases == ("", "")
    assert tuple(service.id for service in normalized.services) == ("",)
    assert tuple(check.id for check in normalized.checks) == ("",)
    assert tuple(task.id for task in normalized.tasks) == ("",)
    assert normalized.diagnostic_inputs.process_cwds[0].id == "process-cwd:"
    assert normalized.diagnostic_inputs.http_checks == (
        HttpDiagnosticSource(
            id="service-check:",
            service_id=None,
            target="http://127.0.0.1:8000/health",
            timeout=2.0,
            attempts=1,
        ),
    )
    assert NormalizedLifecycleProject.model_validate(normalized.model_dump()) == normalized


def test_normalize_lifecycle_v1_projection_is_sorted_safe_and_keeps_no_inferred_relationships(tmp_path: Path) -> None:
    spec = LifecycleSpecV1.model_validate({
        "path": tmp_path / ".agentseek" / "lifecycle.toml",
        "version": 1,
        "template": "example/template",
        "name": "Example",
        "env_file": ".env",
        "tools": {"required": ["zsh", "python"]},
        "paths": {"required": ["frontend/package.json", "README.md"]},
        "env": {
            "Z_KEY": {
                "required": True,
                "default": "never-retain-this-default",
                "description": "Z description",
                "aliases": ["Z_ALIAS", "A_ALIAS"],
            },
            "A_KEY": {
                "default": "",
                "description": "",
                "aliases": ["B_ALIAS", "A_ALIAS"],
            },
        },
        "services": {
            "web": {"url": "http://127.0.0.1:3000"},
            "api": {"url": "http://127.0.0.1:8000"},
        },
        "processes": {
            "worker": {
                "command": ["python", "never-retain-this-command"],
                "cwd": "backend",
            },
        },
        "checks": {
            "probe": {
                "target": "http://127.0.0.1:8000/health",
                "timeout": "2.5",
                "attempts": "3",
            },
        },
        "tasks": {
            "z-task": {"command": ["python", "never-retain-this-command"], "description": ""},
            "build": {"command": ["python", "never-retain-this-command"], "description": "Build."},
        },
    })

    normalized = normalize_lifecycle(spec, project_root=tmp_path)

    assert normalized.environment == (
        NormalizedEnvironmentRequirement(
            name="A_KEY", required=False, description=None, aliases=("A_ALIAS", "B_ALIAS")
        ),
        NormalizedEnvironmentRequirement(
            name="Z_KEY", required=True, description="Z description", aliases=("A_ALIAS", "Z_ALIAS")
        ),
    )
    assert normalized.services == (
        NormalizedService(
            id="api",
            name=None,
            description=None,
            url="http://127.0.0.1:8000",
            kind=None,
            display=None,
            primary=None,
            tech=None,
        ),
        NormalizedService(
            id="web",
            name=None,
            description=None,
            url="http://127.0.0.1:3000",
            kind=None,
            display=None,
            primary=None,
            tech=None,
        ),
    )
    assert normalized.checks == (
        NormalizedCheckDefinition(id="probe", service_id=None, target="http://127.0.0.1:8000/health"),
    )
    assert normalized.tasks == (
        NormalizedTask(id="build", description="Build."),
        NormalizedTask(id="z-task", description=None),
    )
    assert normalized.actions == ()
    assert normalized.services[0].providers == () and normalized.services[0].check_ids == ()
    assert normalized.checks[0].service_id is None
    assert normalized.diagnostic_inputs == DiagnosticInputs(
        env_file=PathDiagnosticSource(id="env-file:.env", path=SafeProjectPath(path=".env")),
        tools=(
            ToolDiagnosticSource(id="tool:python", tool=SafeExecutableName(name="python")),
            ToolDiagnosticSource(id="tool:zsh", tool=SafeExecutableName(name="zsh")),
        ),
        required_paths=(
            PathDiagnosticSource(id="path:README.md", path=SafeProjectPath(path="README.md")),
            PathDiagnosticSource(id="path:frontend/package.json", path=SafeProjectPath(path="frontend/package.json")),
        ),
        process_cwds=(
            PathDiagnosticSource(id="process-cwd:worker", owner_id="worker", path=SafeProjectPath(path="backend")),
        ),
        environment=(
            EnvironmentDiagnosticSource(
                id="env:A_KEY", name="A_KEY", aliases=("A_ALIAS", "B_ALIAS"), required=False, has_usable_default=False
            ),
            EnvironmentDiagnosticSource(
                id="env:Z_KEY", name="Z_KEY", aliases=("A_ALIAS", "Z_ALIAS"), required=True, has_usable_default=True
            ),
        ),
        http_checks=(
            HttpDiagnosticSource(
                id="service-check:probe",
                service_id=None,
                target="http://127.0.0.1:8000/health",
                timeout=2.5,
                attempts=3,
            ),
        ),
    )
    dump = normalized.model_dump_json()
    assert "never-retain-this-command" not in dump
    assert "never-retain-this-default" not in dump


def test_normalize_lifecycle_unsafe_v1_omits_literals_and_keeps_safe_diagnostic_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project-root-sentinel"
    project_root.mkdir()
    (project_root / "symlink-out").symlink_to(tmp_path / "outside", target_is_directory=True)
    spec = LifecycleSpecV1.model_validate({
        **tomllib.loads((FIXTURES / "v1-unsafe-projection.toml").read_text(encoding="utf-8")),
        "path": project_root / ".agentseek" / "lifecycle.toml",
    })

    def forbidden(*_: object, **__: object) -> None:
        raise _ExternalStateAccessed

    with monkeypatch.context() as sentinels:
        sentinels.setattr(socket, "create_connection", forbidden)
        sentinels.setattr(urllib.request, "urlopen", forbidden)
        sentinels.setattr(shutil, "which", forbidden)
        sentinels.setattr(subprocess, "call", forbidden)
        sentinels.setattr(subprocess, "Popen", forbidden)
        sentinels.setattr(subprocess, "run", forbidden)
        sentinels.setattr(Path, "exists", forbidden)
        sentinels.setattr(Path, "is_file", forbidden)

        normalized = normalize_lifecycle(spec, project_root=project_root)

    assert normalized.services == (
        NormalizedService(
            id="api", name=None, description=None, url=None, kind=None, display=None, primary=None, tech=None
        ),
    )
    assert normalized.checks == (NormalizedCheckDefinition(id="probe", service_id=None, target=None),)
    assert normalized.diagnostic_inputs == DiagnosticInputs(
        env_file=PathDiagnosticSource(id="unsafe-path:env-file", path=None),
        tools=(
            ToolDiagnosticSource(id="tool:python", tool=SafeExecutableName(name="python")),
            ToolDiagnosticSource(id="unsafe-path:required-tool:1", source_index=1, tool=None),
        ),
        required_paths=(
            PathDiagnosticSource(id="path:safe-path.txt", path=SafeProjectPath(path="safe-path.txt")),
            PathDiagnosticSource(id="unsafe-path:required:1", source_index=1, path=None),
            PathDiagnosticSource(id="unsafe-path:required:3", source_index=3, path=None),
        ),
        process_cwds=(
            PathDiagnosticSource(id="process-cwd:z-safe", owner_id="z-safe", path=SafeProjectPath(path="safe-cwd")),
            PathDiagnosticSource(id="unsafe-path:process-cwd:0", owner_id="a-unsafe", source_index=0, path=None),
        ),
        unsafe_task_cwd_ids=("unsafe-task",),
        environment=(EnvironmentDiagnosticSource(id="env:API_KEY", name="API_KEY", has_usable_default=True),),
        http_checks=(
            HttpDiagnosticSource(id="service-check:probe", service_id=None, target=None, timeout=2.0, attempts=1),
        ),
    )
    expected_warnings = (
        NormalizationWarning(
            code="duplicate_requirement_collapsed",
            message="Duplicate requirement was collapsed.",
            details={"requirement_type": "path", "first_index": 0, "duplicate_index": 4},
        ),
        NormalizationWarning(
            code="duplicate_requirement_collapsed",
            message="Duplicate requirement was collapsed.",
            details={"requirement_type": "path", "first_index": 1, "duplicate_index": 2},
        ),
        NormalizationWarning(
            code="duplicate_requirement_collapsed",
            message="Duplicate requirement was collapsed.",
            details={"requirement_type": "tool", "first_index": 0, "duplicate_index": 3},
        ),
        NormalizationWarning(
            code="duplicate_requirement_collapsed",
            message="Duplicate requirement was collapsed.",
            details={"requirement_type": "tool", "first_index": 1, "duplicate_index": 2},
        ),
        NormalizationWarning(
            code="lifecycle_v1_metadata_incomplete",
            message="Lifecycle v1 metadata is incomplete.",
            details={},
        ),
        NormalizationWarning(
            code="unsafe_endpoint_omitted",
            message="Unsafe endpoint was omitted.",
            details={"owner_type": "check", "owner_id": "probe", "field": "target"},
        ),
        NormalizationWarning(
            code="unsafe_endpoint_omitted",
            message="Unsafe endpoint was omitted.",
            details={"owner_type": "service", "owner_id": "api", "field": "url"},
        ),
        NormalizationWarning(
            code="unsafe_path_omitted",
            message="Unsafe project path was omitted.",
            details={"owner_type": "env_file", "owner_id": None, "index": None, "field": "env_file"},
        ),
        NormalizationWarning(
            code="unsafe_path_omitted",
            message="Unsafe project path was omitted.",
            details={"owner_type": "process", "owner_id": "a-unsafe", "index": None, "field": "cwd"},
        ),
        NormalizationWarning(
            code="unsafe_path_omitted",
            message="Unsafe project path was omitted.",
            details={"owner_type": "required_path", "owner_id": None, "index": 1, "field": "path"},
        ),
        NormalizationWarning(
            code="unsafe_path_omitted",
            message="Unsafe project path was omitted.",
            details={"owner_type": "required_path", "owner_id": None, "index": 3, "field": "path"},
        ),
        NormalizationWarning(
            code="unsafe_path_omitted",
            message="Unsafe project path was omitted.",
            details={"owner_type": "required_tool", "owner_id": None, "index": 1, "field": "tool"},
        ),
        NormalizationWarning(
            code="unsafe_path_omitted",
            message="Unsafe project path was omitted.",
            details={"owner_type": "task", "owner_id": "unsafe-task", "index": None, "field": "cwd"},
        ),
    )
    assert normalized.warnings == expected_warnings
    assert (
        tuple(
            sorted(
                normalized.warnings,
                key=lambda warning: (
                    warning.code,
                    warning.message,
                    json.dumps(dict(warning.details), separators=(",", ":")),
                ),
            )
        )
        == expected_warnings
    )

    all_source_ids = [
        source.id
        for sources in (
            normalized.diagnostic_inputs.tools,
            normalized.diagnostic_inputs.required_paths,
            normalized.diagnostic_inputs.process_cwds,
            normalized.diagnostic_inputs.environment,
            normalized.diagnostic_inputs.http_checks,
        )
        for source in sources
    ]
    assert normalized.diagnostic_inputs.env_file is not None
    all_source_ids.append(normalized.diagnostic_inputs.env_file.id)
    assert len(all_source_ids) == len(set(all_source_ids))

    dump = normalized.model_dump_json()
    for rejected_literal in (
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
        "project-root-sentinel",
    ):
        assert rejected_literal not in dump


def test_normalize_lifecycle_v2_scalar_reference_projection_is_sorted_and_secret_free(tmp_path: Path) -> None:
    project_root = tmp_path / "project-root-sentinel"
    project_root.mkdir()
    normalized = normalize_lifecycle(_normalized_v2_projection_fixture(project_root), project_root=project_root)

    assert normalized.lifecycle_version == 2
    assert normalized.project == NormalizedProject(
        template="example/normalization",
        name="Projection Project",
        description="",
        guide=NormalizedProjectFile(path="docs/Guide.md"),
    )
    assert normalized.metadata_complete is True
    assert normalized.warnings == ()
    assert normalized.environment == (
        NormalizedEnvironmentRequirement(
            name="A_KEY", required=False, description=None, aliases=("A-other", "z-other")
        ),
        NormalizedEnvironmentRequirement(
            name="Z_KEY", required=True, description=" Z description ", aliases=("A-alias", "z-alias")
        ),
    )
    assert normalized.services == (
        NormalizedService(
            id="api",
            name=" API Service ",
            description=" API description ",
            url="http://127.0.0.1:8000",
            kind="api",
            display="advanced",
            primary=False,
            tech="",
            providers=(
                NormalizedProvider(type="dev", id="process:a-process", process_id="a-process"),
                NormalizedProvider(type="task", id="task:build", task_id="build"),
            ),
            check_ids=("z-api",),
            links=(
                NormalizedReference(rel="api_docs", url="http://127.0.0.1:8000/docs"),
                NormalizedReference(rel="docs", url="https://docs.example.test/guide"),
                NormalizedReference(
                    rel="studio",
                    url="https://studio.example.test/?baseUrl=https%3A%2F%2F127.0.0.1%3A8000",
                ),
            ),
        ),
        NormalizedService(
            id="web",
            name=" Web Application ",
            description=" Web description ",
            url="http://127.0.0.1:5173",
            kind="web",
            display="default",
            primary=True,
            tech=None,
            providers=(
                NormalizedProvider(type="dev", id="process:z-process", process_id="z-process"),
                NormalizedProvider(type="task", id="task:z-task", task_id="z-task"),
            ),
            check_ids=("web",),
        ),
    )
    assert normalized.checks == (
        NormalizedCheckDefinition(id="web", service_id="web", target="http://127.0.0.1:5173/health"),
        NormalizedCheckDefinition(id="z-api", service_id="api", target="http://127.0.0.1:8000/health"),
    )
    assert normalized.tasks == (
        NormalizedTask(id="build", description=" Build description ", starts=("api",)),
        NormalizedTask(id="z-task", description=None, starts=("web",), stops=("api",)),
    )
    assert normalized.actions == (
        NormalizedAction(id="project:start_dev", type="start_dev", label="Start development"),
        NormalizedAction(
            id="service:api:copy",
            type="copy_endpoint",
            label="Copy  API Service  endpoint",
            service_id="api",
            url="http://127.0.0.1:8000",
        ),
        NormalizedAction(
            id="service:api:reference:api_docs",
            type="open_reference",
            label="Open  API Service  api_docs",
            service_id="api",
            url="http://127.0.0.1:8000/docs",
            reference_rel="api_docs",
        ),
        NormalizedAction(
            id="service:api:reference:docs",
            type="open_reference",
            label="Open  API Service  docs",
            service_id="api",
            url="https://docs.example.test/guide",
            reference_rel="docs",
        ),
        NormalizedAction(
            id="service:api:reference:studio",
            type="open_reference",
            label="Open  API Service  studio",
            service_id="api",
            url="https://studio.example.test/?baseUrl=https%3A%2F%2F127.0.0.1%3A8000",
            reference_rel="studio",
        ),
        NormalizedAction(
            id="service:web:open",
            type="open_url",
            label="Open  Web Application ",
            service_id="web",
            url="http://127.0.0.1:5173",
        ),
        NormalizedAction(id="task:build", type="run_task", label="Run task build", task_id="build"),
        NormalizedAction(id="task:z-task", type="run_task", label="Run task z-task", task_id="z-task"),
    )

    dump = normalized.model_dump_json()
    for forbidden_literal in (
        "process-command-sentinel",
        "another-process-command-sentinel",
        "task-command-sentinel",
        "another-task-command-sentinel",
        "task-cwd-sentinel",
        "environment-default-sentinel",
        "loader-path-sentinel",
        "project-root-sentinel",
    ):
        assert forbidden_literal not in dump


def test_normalize_lifecycle_v2_safe_diagnostic_inputs_are_relative_and_sorted(tmp_path: Path) -> None:
    project_root = tmp_path / "project-root-sentinel"
    project_root.mkdir()
    normalized = normalize_lifecycle(_normalized_v2_projection_fixture(project_root), project_root=project_root)

    assert normalized.diagnostic_inputs == DiagnosticInputs(
        env_file=PathDiagnosticSource(id="env-file:.env", path=SafeProjectPath(path=".env")),
        tools=(
            ToolDiagnosticSource(id="tool:python", tool=SafeExecutableName(name="python")),
            ToolDiagnosticSource(id="tool:zsh", tool=SafeExecutableName(name="zsh")),
        ),
        required_paths=(
            PathDiagnosticSource(id="path:README.md", path=SafeProjectPath(path="README.md")),
            PathDiagnosticSource(id="path:z/path", path=SafeProjectPath(path="z/path")),
        ),
        process_cwds=(
            PathDiagnosticSource(
                id="process-cwd:a-process", owner_id="a-process", path=SafeProjectPath(path="backend")
            ),
            PathDiagnosticSource(id="process-cwd:z-process", owner_id="z-process", path=SafeProjectPath(path=".")),
        ),
        environment=(
            EnvironmentDiagnosticSource(
                id="env:A_KEY", name="A_KEY", aliases=("A-other", "z-other"), required=False, has_usable_default=False
            ),
            EnvironmentDiagnosticSource(
                id="env:Z_KEY", name="Z_KEY", aliases=("A-alias", "z-alias"), required=True, has_usable_default=True
            ),
        ),
        http_checks=(
            HttpDiagnosticSource(
                id="service-check:web", service_id="web", target="http://127.0.0.1:5173/health", timeout=3.5, attempts=5
            ),
            HttpDiagnosticSource(
                id="service-check:z-api",
                service_id="api",
                target="http://127.0.0.1:8000/health",
                timeout=4.5,
                attempts=6,
            ),
        ),
    )


@pytest.mark.parametrize("path_field", ["guide", "env_file", "required_path", "process_cwd", "task_cwd"])
def test_normalize_lifecycle_v2_reconfines_every_path_against_supplied_root(tmp_path: Path, path_field: str) -> None:
    authored_root = tmp_path / "authored-root"
    normalization_root = tmp_path / "normalization-root"
    outside_root = tmp_path / "outside-root"
    authored_root.mkdir()
    normalization_root.mkdir()
    outside_root.mkdir()
    (authored_root / "escape").mkdir()
    (normalization_root / "escape").symlink_to(outside_root, target_is_directory=True)
    data: dict[str, object] = {
        "version": 2,
        "template": "example/path-revalidation",
        "name": "Path Revalidation",
        "processes": {"app": {"command": ["python", "app.py"]}},
        "tasks": {},
    }
    if path_field in {"guide", "env_file"}:
        data[path_field] = "escape"
    elif path_field == "required_path":
        data["paths"] = {"required": ["escape"]}
    elif path_field == "process_cwd":
        data["processes"] = {"app": {"command": ["python", "app.py"], "cwd": "escape"}}
    else:
        data["tasks"] = {"run": {"command": ["python", "task.py"], "cwd": "escape"}}
    spec = LifecycleSpecV2.model_validate(
        data,
        context={
            "project_root": authored_root,
            "loader_path": authored_root / ".agentseek" / "lifecycle.toml",
        },
    )

    with pytest.raises(UnsafeProjectPathError) as exc_info:
        normalize_lifecycle(spec, project_root=normalization_root)

    assert str(exc_info.value) == "project path is unsafe"
    rendered = str(exc_info.value)
    assert "escape" not in rendered
    assert str(authored_root.resolve()) not in rendered
    assert str(normalization_root.resolve()) not in rendered
    assert str(outside_root.resolve()) not in rendered


def test_normalize_lifecycle_v2_explicit_relationships_suppress_same_id_inference(tmp_path: Path) -> None:
    spec = LifecycleSpecV2.model_validate(
        {
            "version": 2,
            "template": "example/explicit-precedence",
            "name": "Explicit Precedence",
            "services": {
                "app": {
                    "name": "Application",
                    "url": "http://127.0.0.1:8000",
                    "kind": "web",
                    "primary": True,
                    "description": "Application.",
                },
                "other": {
                    "name": "Other API",
                    "url": "http://127.0.0.1:8100",
                    "kind": "api",
                    "description": "Other service.",
                },
                "empty": {
                    "name": "Unprovided service",
                    "url": "http://127.0.0.1:8200",
                    "kind": "api",
                    "description": "Explicitly unprovided.",
                },
            },
            "processes": {
                "app": {"command": ["python", "app.py"], "provides": ["other"]},
                "empty": {"command": ["python", "empty.py"], "provides": []},
            },
            "checks": {"app": {"target": "http://127.0.0.1:8100/health", "service": "other"}},
        },
        context={
            "project_root": tmp_path,
            "loader_path": tmp_path / ".agentseek" / "lifecycle.toml",
        },
    )

    normalized = normalize_lifecycle(spec, project_root=tmp_path)

    services = {service.id: service for service in normalized.services}
    assert services["app"].providers == ()
    assert services["app"].check_ids == ()
    assert services["empty"].providers == ()
    assert services["other"].providers == (NormalizedProvider(type="dev", id="process:app", process_id="app"),)
    assert services["other"].check_ids == ("app",)
    assert normalized.checks == (
        NormalizedCheckDefinition(id="app", service_id="other", target="http://127.0.0.1:8100/health"),
    )


@pytest.mark.parametrize(
    ("fixture_name", "expected_provider_ids", "expected_check_ids", "expected_task_effects", "expected_action_ids"),
    [
        (
            "v2-same-id.toml",
            {"app": ("process:app",)},
            {"app": ("app",)},
            {},
            ("project:start_dev", "service:app:open"),
        ),
        (
            "v2-bub-explicit.toml",
            {"app": ("process:frontend",), "copilotkit": ("process:frontend",), "gateway": ("process:gateway",)},
            {"app": ("frontend",), "copilotkit": (), "gateway": ("gateway",)},
            {},
            ("project:start_dev", "service:app:open", "service:gateway:copy", "service:gateway:reference:docs"),
        ),
        (
            "v2-service-free.toml",
            {},
            {},
            {"seed": ((), ())},
            (),
        ),
        (
            "v2-task-providers.toml",
            {"app": ("process:app", "task:stack"), "database": ("task:stack",)},
            {"app": (), "database": ()},
            {"stack": (("app", "database"), ()), "stack-stop": ((), ("app", "database"))},
            ("project:start_dev", "service:app:open", "service:database:copy", "task:stack", "task:stack-stop"),
        ),
    ],
)
def test_normalize_lifecycle_v2_topology_fixture_relationships_and_actions(
    tmp_path: Path,
    fixture_name: str,
    expected_provider_ids: dict[str, tuple[str, ...]],
    expected_check_ids: dict[str, tuple[str, ...]],
    expected_task_effects: dict[str, tuple[tuple[str, ...], tuple[str, ...]]],
    expected_action_ids: tuple[str, ...],
) -> None:
    project_root = tmp_path / "project-root-sentinel"
    project_root.mkdir()
    spec = LifecycleSpecV2.model_validate(
        tomllib.loads((FIXTURES / fixture_name).read_text(encoding="utf-8")),
        context={
            "project_root": project_root,
            "loader_path": project_root / ".agentseek" / "loader-path-sentinel.toml",
        },
    )

    normalized = normalize_lifecycle(spec, project_root=project_root)

    assert {
        service.id: tuple(provider.id for provider in service.providers) for service in normalized.services
    } == expected_provider_ids
    assert {service.id: service.check_ids for service in normalized.services} == expected_check_ids
    assert {task.id: (task.starts, task.stops) for task in normalized.tasks} == expected_task_effects
    assert tuple(action.id for action in normalized.actions) == expected_action_ids
    assert tuple(action.id for action in normalized.actions) == tuple(
        sorted(action.id for action in normalized.actions)
    )


def test_normalize_lifecycle_v2_action_fields_are_normative_for_same_id_fixture(tmp_path: Path) -> None:
    project_root = tmp_path / "project-root-sentinel"
    project_root.mkdir()
    spec = LifecycleSpecV2.model_validate(
        tomllib.loads((FIXTURES / "v2-same-id.toml").read_text(encoding="utf-8")),
        context={
            "project_root": project_root,
            "loader_path": project_root / ".agentseek" / "loader-path-sentinel.toml",
        },
    )

    normalized = normalize_lifecycle(spec, project_root=project_root)

    assert normalized.services[0].providers == (NormalizedProvider(type="dev", id="process:app", process_id="app"),)
    assert normalized.services[0].check_ids == ("app",)
    assert normalized.checks == (
        NormalizedCheckDefinition(id="app", service_id="app", target="http://127.0.0.1:8000/health"),
    )
    assert normalized.diagnostic_inputs.http_checks[0].service_id == "app"
    assert normalized.actions == (
        NormalizedAction(id="project:start_dev", type="start_dev", label="Start development"),
        NormalizedAction(
            id="service:app:open",
            type="open_url",
            label="Open Application",
            service_id="app",
            url="http://127.0.0.1:8000",
        ),
    )


def test_normalize_lifecycle_v2_hidden_only_process_provider_does_not_start_dev(tmp_path: Path) -> None:
    project_root = tmp_path / "project-root-sentinel"
    project_root.mkdir()
    spec = LifecycleSpecV2.model_validate(
        {
            "version": 2,
            "template": "example/hidden-provider",
            "name": "Hidden Provider Project",
            "services": {
                "app": {
                    "name": "Application",
                    "url": "http://127.0.0.1:8000",
                    "kind": "web",
                    "primary": True,
                    "description": "Visible application.",
                },
                "internal": {
                    "name": "Internal API",
                    "url": "http://127.0.0.1:8100",
                    "kind": "api",
                    "display": "hidden",
                    "description": "Hidden implementation service.",
                },
            },
            "processes": {"internal": {"command": ["python", "internal.py"]}},
        },
        context={
            "project_root": project_root,
            "loader_path": project_root / ".agentseek" / "loader-path-sentinel.toml",
        },
    )

    normalized = normalize_lifecycle(spec, project_root=project_root)

    assert normalized.services[0].providers == ()
    assert normalized.services[1].providers == (
        NormalizedProvider(type="dev", id="process:internal", process_id="internal"),
    )
    assert normalized.actions == (
        NormalizedAction(
            id="service:app:open",
            type="open_url",
            label="Open Application",
            service_id="app",
            url="http://127.0.0.1:8000",
        ),
    )
    assert "project:start_dev" not in {action.id for action in normalized.actions}


def test_normalize_lifecycle_v2_topology_deduplicates_edges_and_actions_stably(tmp_path: Path) -> None:
    project_root = tmp_path / "project-root-sentinel"
    project_root.mkdir()

    normalized = normalize_lifecycle(_v2_topology_spec(project_root), project_root=project_root)
    reversed_normalized = normalize_lifecycle(_v2_topology_spec(project_root, reverse=True), project_root=project_root)

    assert normalized.model_dump_json() == reversed_normalized.model_dump_json()
    assert normalized.services == (
        NormalizedService(
            id="api",
            name="API",
            description="Application API.",
            url="http://127.0.0.1:8100",
            kind="api",
            display="advanced",
            primary=False,
            tech=None,
            providers=(
                NormalizedProvider(type="dev", id="process:alpha", process_id="alpha"),
                NormalizedProvider(type="task", id="task:multi", task_id="multi"),
            ),
            check_ids=("api-probe",),
            links=(
                NormalizedReference(rel="api_docs", url="https://docs.example.test/api/openapi"),
                NormalizedReference(rel="docs", url="https://docs.example.test/api"),
                NormalizedReference(
                    rel="studio", url="https://studio.example.test/?baseUrl=https%3A%2F%2F127.0.0.1%3A8100"
                ),
            ),
        ),
        NormalizedService(
            id="app",
            name="Application",
            description="Browser application.",
            url="http://127.0.0.1:8000",
            kind="web",
            display="default",
            primary=True,
            tech=None,
            providers=(
                NormalizedProvider(type="dev", id="process:alpha", process_id="alpha"),
                NormalizedProvider(type="dev", id="process:bravo", process_id="bravo"),
                NormalizedProvider(type="task", id="task:multi", task_id="multi"),
            ),
            check_ids=("app",),
        ),
        NormalizedService(
            id="database",
            name="Database",
            description="Application database.",
            url="mysql://127.0.0.1:3306/app",
            kind="database",
            display="default",
            primary=False,
            tech=None,
        ),
        NormalizedService(
            id="other",
            name="Other service",
            description="No endpoint action.",
            url="http://127.0.0.1:8200",
            kind="other",
            display="advanced",
            primary=False,
            tech=None,
        ),
        NormalizedService(
            id="protocol",
            name="Hidden protocol",
            description="Internal protocol service.",
            url="http://127.0.0.1:8300",
            kind="protocol",
            display="hidden",
            primary=False,
            tech=None,
            providers=(
                NormalizedProvider(type="dev", id="process:hidden", process_id="hidden"),
                NormalizedProvider(type="task", id="task:hidden-only", task_id="hidden-only"),
            ),
        ),
    )
    assert normalized.checks == (
        NormalizedCheckDefinition(id="api-probe", service_id="api", target="http://127.0.0.1:8100/health"),
        NormalizedCheckDefinition(id="app", service_id="app", target="http://127.0.0.1:8000/health"),
    )
    assert normalized.tasks == (
        NormalizedTask(id="hidden-only", description=None, starts=("protocol",), stops=("protocol",)),
        NormalizedTask(id="multi", description=None, starts=("api", "app"), stops=("database",)),
    )
    assert normalized.actions == (
        NormalizedAction(id="project:start_dev", type="start_dev", label="Start development"),
        NormalizedAction(
            id="service:api:copy",
            type="copy_endpoint",
            label="Copy API endpoint",
            service_id="api",
            url="http://127.0.0.1:8100",
        ),
        NormalizedAction(
            id="service:api:reference:api_docs",
            type="open_reference",
            label="Open API api_docs",
            service_id="api",
            url="https://docs.example.test/api/openapi",
            reference_rel="api_docs",
        ),
        NormalizedAction(
            id="service:api:reference:docs",
            type="open_reference",
            label="Open API docs",
            service_id="api",
            url="https://docs.example.test/api",
            reference_rel="docs",
        ),
        NormalizedAction(
            id="service:api:reference:studio",
            type="open_reference",
            label="Open API studio",
            service_id="api",
            url="https://studio.example.test/?baseUrl=https%3A%2F%2F127.0.0.1%3A8100",
            reference_rel="studio",
        ),
        NormalizedAction(
            id="service:app:open",
            type="open_url",
            label="Open Application",
            service_id="app",
            url="http://127.0.0.1:8000",
        ),
        NormalizedAction(
            id="service:database:copy",
            type="copy_endpoint",
            label="Copy Database endpoint",
            service_id="database",
            url="mysql://127.0.0.1:3306/app",
        ),
        NormalizedAction(id="task:multi", type="run_task", label="Run task multi", task_id="multi"),
    )


def test_normalize_lifecycle_v1_is_deterministic_across_authored_map_order(tmp_path: Path) -> None:
    project_root = tmp_path / "project-root-sentinel"
    project_root.mkdir()
    common = {
        "path": project_root / ".agentseek" / "lifecycle.toml",
        "version": 1,
        "template": "example/deterministic-v1",
        "name": "Deterministic v1",
        "tools": {"required": ["python", "zsh"]},
        "paths": {"required": ["README.md", "frontend/package.json"]},
    }
    first = LifecycleSpecV1.model_validate({
        **common,
        "env": {
            "Z_KEY": {"required": True, "aliases": ["Z_ALIAS", "A_ALIAS"]},
            "A_KEY": {"required": False, "aliases": ["B_ALIAS", "A_ALIAS"]},
        },
        "services": {
            "web": {"url": "http://127.0.0.1:3000"},
            "api": {"url": "http://127.0.0.1:8000"},
        },
        "processes": {
            "worker": {"command": ["python", "worker.py"], "cwd": "backend"},
            "app": {"command": ["python", "app.py"]},
        },
        "checks": {
            "web": {"target": "http://127.0.0.1:3000/health"},
            "api": {"target": "http://127.0.0.1:8000/health"},
        },
        "tasks": {
            "z-task": {"command": ["python", "z.py"], "description": "Z task."},
            "build": {"command": ["python", "build.py"], "description": "Build."},
        },
    })
    second = LifecycleSpecV1.model_validate({
        **common,
        "env": {
            "A_KEY": {"required": False, "aliases": ["B_ALIAS", "A_ALIAS"]},
            "Z_KEY": {"required": True, "aliases": ["Z_ALIAS", "A_ALIAS"]},
        },
        "services": {
            "api": {"url": "http://127.0.0.1:8000"},
            "web": {"url": "http://127.0.0.1:3000"},
        },
        "processes": {
            "app": {"command": ["python", "app.py"]},
            "worker": {"command": ["python", "worker.py"], "cwd": "backend"},
        },
        "checks": {
            "api": {"target": "http://127.0.0.1:8000/health"},
            "web": {"target": "http://127.0.0.1:3000/health"},
        },
        "tasks": {
            "build": {"command": ["python", "build.py"], "description": "Build."},
            "z-task": {"command": ["python", "z.py"], "description": "Z task."},
        },
    })

    first_normalized = normalize_lifecycle(first, project_root=project_root)
    second_normalized = normalize_lifecycle(second, project_root=project_root)

    assert first_normalized.model_dump() == second_normalized.model_dump()
    assert first_normalized.model_dump_json() == second_normalized.model_dump_json()


def test_normalize_lifecycle_is_independent_of_environment_and_env_file_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_root = tmp_path / "project-root-sentinel"
    project_root.mkdir()
    env_file = project_root / ".env"
    spec = LifecycleSpecV1.model_validate({
        "path": project_root / ".agentseek" / "lifecycle.toml",
        "version": 1,
        "template": "example/secret-free",
        "name": "Secret-free v1",
        "env_file": ".env",
        "env": {
            "API_KEY": {
                "required": True,
                "default": "AUTHORED_DEFAULT_SECRET_SENTINEL",
                "description": "API key requirement.",
            }
        },
        "processes": {"app": {"command": ["python", "RAW_COMMAND_SECRET_SENTINEL"]}},
    })

    monkeypatch.setenv("API_KEY", "SHELL_SECRET_SENTINEL_ONE")
    env_file.write_text("API_KEY=DOTENV_SECRET_SENTINEL_ONE\n", encoding="utf-8")
    first = normalize_lifecycle(spec, project_root=project_root)
    monkeypatch.setenv("API_KEY", "SHELL_SECRET_SENTINEL_TWO")
    env_file.write_text("API_KEY=DOTENV_SECRET_SENTINEL_TWO\n", encoding="utf-8")
    second = normalize_lifecycle(spec, project_root=project_root)

    assert first.model_dump() == second.model_dump()
    assert first.model_dump_json() == second.model_dump_json()
    recursive_dump = json.dumps(first.model_dump(), ensure_ascii=False, sort_keys=True)
    for sentinel in (
        "AUTHORED_DEFAULT_SECRET_SENTINEL",
        "RAW_COMMAND_SECRET_SENTINEL",
        "SHELL_SECRET_SENTINEL_ONE",
        "SHELL_SECRET_SENTINEL_TWO",
        "DOTENV_SECRET_SENTINEL_ONE",
        "DOTENV_SECRET_SENTINEL_TWO",
        str(project_root.resolve()),
    ):
        assert sentinel not in recursive_dump


def _normalized_v1_dump(project_root: Path) -> dict[str, Any]:
    spec = LifecycleSpecV1.model_validate({
        "path": project_root / ".agentseek" / "lifecycle.toml",
        "version": 1,
        "name": "Legacy Project",
        "processes": {"app": {"command": ["python", "app.py"]}},
    })
    return normalize_lifecycle(spec, project_root=project_root).model_dump()


def _normalized_v2_dump(project_root: Path) -> dict[str, Any]:
    return normalize_lifecycle(_normalized_v2_projection_fixture(project_root), project_root=project_root).model_dump()


def _normalized_unsafe_v1_dump(project_root: Path) -> dict[str, Any]:
    (project_root / "symlink-out").symlink_to(project_root.parent / "outside", target_is_directory=True)
    spec = LifecycleSpecV1.model_validate({
        **tomllib.loads((FIXTURES / "v1-unsafe-projection.toml").read_text(encoding="utf-8")),
        "path": project_root / ".agentseek" / "lifecycle.toml",
    })
    return normalize_lifecycle(spec, project_root=project_root).model_dump()


def _warning_payload_sort_key(warning: Mapping[str, Any]) -> tuple[str, str, str]:
    return (
        warning["code"],
        warning["message"],
        json.dumps(dict(warning["details"]), ensure_ascii=False, separators=(",", ":")),
    )


def _warning_payload(code: WarningCode, details: dict[str, str | int | None]) -> dict[str, object]:
    messages = {
        "lifecycle_v1_metadata_incomplete": "Lifecycle v1 metadata is incomplete.",
        "unsafe_endpoint_omitted": "Unsafe endpoint was omitted.",
        "unsafe_path_omitted": "Unsafe project path was omitted.",
        "duplicate_requirement_collapsed": "Duplicate requirement was collapsed.",
    }
    return {"code": code, "message": messages[code], "details": details}


def _payload_matches_warning(
    warning: Mapping[str, Any], code: WarningCode, details: Mapping[str, str | int | None]
) -> bool:
    return warning["code"] == code and warning["details"] == details


def test_exported_root_rejects_v1_without_process_diagnostic_sources(tmp_path: Path) -> None:
    data = _normalized_v1_dump(tmp_path)
    data["diagnostic_inputs"]["process_cwds"] = []

    with pytest.raises(ValidationError):
        NormalizedLifecycleProject.model_validate(data)


def test_exported_root_rejects_service_free_v2_without_process_diagnostic_sources(tmp_path: Path) -> None:
    project_root = tmp_path / "service-free"
    project_root.mkdir()
    spec = LifecycleSpecV2.model_validate(
        tomllib.loads((FIXTURES / "v2-service-free.toml").read_text(encoding="utf-8")),
        context={
            "project_root": project_root,
            "loader_path": project_root / ".agentseek" / "lifecycle.toml",
        },
    )
    data = normalize_lifecycle(spec, project_root=project_root).model_dump()
    data["diagnostic_inputs"]["process_cwds"] = []

    with pytest.raises(ValidationError):
        NormalizedLifecycleProject.model_validate(data)


def test_exported_root_rejects_v1_unsafe_process_source_with_noncanonical_sorted_owner_index(
    tmp_path: Path,
) -> None:
    spec = LifecycleSpecV1.model_validate({
        "path": tmp_path / ".agentseek" / "lifecycle.toml",
        "version": 1,
        "name": "Unsafe process",
        "processes": {"app": {"command": ["python", "app.py"], "cwd": "../outside"}},
    })
    data = normalize_lifecycle(spec, project_root=tmp_path).model_dump()
    source = data["diagnostic_inputs"]["process_cwds"][0]
    source["id"] = "unsafe-path:process-cwd:99"
    source["source_index"] = 99

    with pytest.raises(ValidationError):
        NormalizedLifecycleProject.model_validate(data)


@pytest.mark.parametrize(
    "invalid_state",
    [
        "missing_service_warning",
        "ghost_service_warning",
        "warning_for_present_service",
        "missing_check_warning",
        "ghost_check_warning",
        "warning_for_present_check",
        "missing_env_file_warning",
        "warning_for_present_env_file",
        "missing_required_path_warning",
        "missing_required_tool_warning",
        "missing_process_warning",
        "ghost_required_path_warning",
        "ghost_process_warning",
        "ghost_task_warning",
    ],
)
def test_exported_root_rejects_v1_omission_warning_reciprocity_violations(
    tmp_path: Path,
    invalid_state: str,
) -> None:
    project_root = tmp_path / "unsafe-v1"
    project_root.mkdir()
    data = _normalized_unsafe_v1_dump(project_root)
    warning_targets: dict[str, tuple[WarningCode, dict[str, str | int | None]]] = {
        "service": (
            "unsafe_endpoint_omitted",
            {"owner_type": "service", "owner_id": "api", "field": "url"},
        ),
        "check": (
            "unsafe_endpoint_omitted",
            {"owner_type": "check", "owner_id": "probe", "field": "target"},
        ),
        "env_file": (
            "unsafe_path_omitted",
            {"owner_type": "env_file", "owner_id": None, "index": None, "field": "env_file"},
        ),
        "required_path": (
            "unsafe_path_omitted",
            {"owner_type": "required_path", "owner_id": None, "index": 1, "field": "path"},
        ),
        "required_tool": (
            "unsafe_path_omitted",
            {"owner_type": "required_tool", "owner_id": None, "index": 1, "field": "tool"},
        ),
        "process": (
            "unsafe_path_omitted",
            {"owner_type": "process", "owner_id": "a-unsafe", "index": None, "field": "cwd"},
        ),
        "task": (
            "unsafe_path_omitted",
            {"owner_type": "task", "owner_id": "unsafe-task", "index": None, "field": "cwd"},
        ),
    }
    warnings = data["warnings"]

    if invalid_state.startswith("missing_"):
        owner = invalid_state.removeprefix("missing_").removesuffix("_warning")
        code, details = warning_targets[owner]
        data["warnings"] = [warning for warning in warnings if not _payload_matches_warning(warning, code, details)]
    elif invalid_state == "ghost_service_warning":
        data["warnings"] = [
            *warnings,
            _warning_payload(
                "unsafe_endpoint_omitted",
                {"owner_type": "service", "owner_id": "missing-service", "field": "url"},
            ),
        ]
    elif invalid_state == "ghost_check_warning":
        data["warnings"] = [
            *warnings,
            _warning_payload(
                "unsafe_endpoint_omitted",
                {"owner_type": "check", "owner_id": "missing-check", "field": "target"},
            ),
        ]
    elif invalid_state == "ghost_required_path_warning":
        data["warnings"] = [
            *warnings,
            _warning_payload(
                "unsafe_path_omitted",
                {"owner_type": "required_path", "owner_id": None, "index": 99, "field": "path"},
            ),
        ]
    elif invalid_state == "ghost_process_warning":
        data["warnings"] = [
            *warnings,
            _warning_payload(
                "unsafe_path_omitted",
                {"owner_type": "process", "owner_id": "missing-process", "index": None, "field": "cwd"},
            ),
        ]
    elif invalid_state == "ghost_task_warning":
        data["warnings"] = [
            *warnings,
            _warning_payload(
                "unsafe_path_omitted",
                {"owner_type": "task", "owner_id": "missing-task", "index": None, "field": "cwd"},
            ),
        ]
    elif invalid_state == "warning_for_present_service":
        data["services"][0]["url"] = "http://127.0.0.1:8000"
    elif invalid_state == "warning_for_present_check":
        data["checks"][0]["target"] = "http://127.0.0.1:8000/health"
        data["diagnostic_inputs"]["http_checks"][0]["target"] = data["checks"][0]["target"]
    else:
        data["diagnostic_inputs"]["env_file"] = {
            "id": "env-file:.env",
            "owner_id": None,
            "source_index": None,
            "path": {"path": ".env"},
        }

    data["warnings"] = sorted(data["warnings"], key=_warning_payload_sort_key)
    with pytest.raises(ValidationError):
        NormalizedLifecycleProject.model_validate(data)


@pytest.mark.parametrize(
    ("code", "details"),
    [
        ("unsafe_endpoint_omitted", {"owner_type": "service", "owner_id": "api", "field": "url"}),
        ("unsafe_endpoint_omitted", {"owner_type": "check", "owner_id": "probe", "field": "target"}),
        (
            "unsafe_path_omitted",
            {"owner_type": "env_file", "owner_id": None, "index": None, "field": "env_file"},
        ),
        (
            "unsafe_path_omitted",
            {"owner_type": "required_path", "owner_id": None, "index": 1, "field": "path"},
        ),
        (
            "unsafe_path_omitted",
            {"owner_type": "required_tool", "owner_id": None, "index": 1, "field": "tool"},
        ),
        (
            "unsafe_path_omitted",
            {"owner_type": "process", "owner_id": "a-unsafe", "index": None, "field": "cwd"},
        ),
        (
            "unsafe_path_omitted",
            {"owner_type": "task", "owner_id": "unsafe-task", "index": None, "field": "cwd"},
        ),
    ],
)
def test_exported_root_preserves_duplicate_matching_v1_omission_warnings(
    tmp_path: Path,
    code: WarningCode,
    details: dict[str, str | int | None],
) -> None:
    project_root = tmp_path / "unsafe-v1"
    project_root.mkdir()
    data = _normalized_unsafe_v1_dump(project_root)
    duplicate = next(warning.copy() for warning in data["warnings"] if _payload_matches_warning(warning, code, details))
    data["warnings"] = sorted([*data["warnings"], duplicate], key=_warning_payload_sort_key)

    validated = NormalizedLifecycleProject.model_validate(data)

    expected = NormalizationWarning.model_validate(duplicate)
    assert validated.warnings.count(expected) == 2


def test_exported_root_still_rejects_duplicate_v1_metadata_warning(tmp_path: Path) -> None:
    data = _normalized_v1_dump(tmp_path)
    duplicate = next(
        warning.copy() for warning in data["warnings"] if warning["code"] == "lifecycle_v1_metadata_incomplete"
    )
    data["warnings"] = sorted([*data["warnings"], duplicate], key=_warning_payload_sort_key)

    with pytest.raises(ValidationError):
        NormalizedLifecycleProject.model_validate(data)


@pytest.mark.parametrize("copy_method", ["model_copy", "deepcopy", "pickle"])
def test_exported_v1_root_supports_deep_copy_and_pickle(tmp_path: Path, copy_method: str) -> None:
    project = NormalizedLifecycleProject.model_validate(_normalized_v1_dump(tmp_path))

    if copy_method == "model_copy":
        copied = project.model_copy(deep=True)
    elif copy_method == "deepcopy":
        copied = copy.deepcopy(project)
    else:
        copied = pickle.loads(pickle.dumps(project))  # noqa: S301 - round-trip trusted in-memory bytes

    assert copied == project
    assert copied is not project
    assert type(copied.warnings[0].details) is MappingProxyType


@pytest.mark.parametrize("copy_method", ["model_copy", "deepcopy"])
def test_warning_deep_copy_recursively_copies_subclass_state(copy_method: str) -> None:
    class ExtendedWarning(NormalizationWarning):
        tags: list[str]
        _private_tags: list[str] = PrivateAttr(default_factory=list)

    warning = ExtendedWarning(
        code="lifecycle_v1_metadata_incomplete",
        message="Lifecycle v1 metadata is incomplete.",
        details={},
        tags=["public"],
    )
    warning._private_tags.append("private")

    copied = warning.model_copy(deep=True) if copy_method == "model_copy" else copy.deepcopy(warning)
    copied.tags.append("copied")
    copied._private_tags.append("copied")

    assert warning.tags == ["public"]
    assert warning._private_tags == ["private"]
    assert type(copied.details) is MappingProxyType


@pytest.mark.parametrize("invalid_state", ["missing_unsafe_warning", "warning_for_safe_task"])
def test_exported_root_rejects_v1_task_warning_provenance_mismatch(
    tmp_path: Path,
    invalid_state: str,
) -> None:
    spec = LifecycleSpecV1.model_validate({
        "path": tmp_path / ".agentseek" / "lifecycle.toml",
        "version": 1,
        "name": "Task warning provenance",
        "processes": {"app": {"command": ["python", "app.py"]}},
        "tasks": {
            "safe-task": {"command": ["python", "safe.py"], "cwd": "."},
            "unsafe-task": {"command": ["python", "unsafe.py"], "cwd": "../outside"},
        },
    })
    data = normalize_lifecycle(spec, project_root=tmp_path).model_dump()
    unsafe_details = {"owner_type": "task", "owner_id": "unsafe-task", "index": None, "field": "cwd"}
    if invalid_state == "missing_unsafe_warning":
        data["warnings"] = [
            warning
            for warning in data["warnings"]
            if not _payload_matches_warning(warning, "unsafe_path_omitted", unsafe_details)
        ]
    else:
        data["warnings"] = sorted(
            [
                *data["warnings"],
                _warning_payload(
                    "unsafe_path_omitted",
                    {"owner_type": "task", "owner_id": "safe-task", "index": None, "field": "cwd"},
                ),
            ],
            key=_warning_payload_sort_key,
        )

    with pytest.raises(ValidationError):
        NormalizedLifecycleProject.model_validate(data)


@pytest.mark.parametrize("invalid_state", ["metadata_complete", "actions"])
def test_exported_root_rejects_v1_complete_metadata_or_actions(tmp_path: Path, invalid_state: str) -> None:
    data = _normalized_v1_dump(tmp_path)
    if invalid_state == "metadata_complete":
        data["metadata_complete"] = True
    else:
        data["actions"] = [
            {
                "id": "project:start_dev",
                "type": "start_dev",
                "label": "Start development",
                "service_id": None,
                "url": None,
                "reference_rel": None,
                "task_id": None,
            }
        ]

    with pytest.raises(ValidationError):
        NormalizedLifecycleProject.model_validate(data)


@pytest.mark.parametrize(
    "invalid_state",
    [
        "absolute_guide",
        "traversing_diagnostic_path",
        "dot_env_file",
        "dot_required_path",
        "unsafe_executable",
        "unsafe_service_url",
        "unsafe_reference_url",
        "unsafe_check_url",
        "duplicate_service_ids",
        "unsorted_service_ids",
        "invalid_v2_identifier",
        "duplicate_environment_names",
        "unsorted_environment_names",
        "duplicate_action_ids",
        "unsorted_action_ids",
        "duplicate_providers",
        "unsorted_providers",
        "duplicate_link_relations",
        "unsorted_links",
        "unsorted_aliases",
        "unsorted_warnings",
        "duplicate_diagnostic_ids",
        "unsorted_diagnostics",
        "http_diagnostic_mismatch",
        "nonpositive_http_attempts",
        "dangling_check",
        "check_reciprocity_mismatch",
        "dangling_task_effect",
        "dangling_dev_provider",
        "dangling_task_provider",
        "noncanonical_action_label",
        "hidden_service_action",
        "missing_primary",
        "metadata_incomplete",
        "v2_warning",
        "missing_template",
    ],
)
def test_exported_root_rejects_unsafe_or_noncanonical_v2_states(tmp_path: Path, invalid_state: str) -> None:  # noqa: C901
    project_root = tmp_path / "project"
    project_root.mkdir()
    data = _normalized_v2_dump(project_root)
    if invalid_state == "absolute_guide":
        data["project"]["guide"]["path"] = "/private/unsafe-guide"
    elif invalid_state == "traversing_diagnostic_path":
        data["diagnostic_inputs"]["required_paths"][0]["path"]["path"] = "../unsafe"
    elif invalid_state == "dot_env_file":
        data["diagnostic_inputs"]["env_file"] = {
            "id": "env-file:.",
            "owner_id": None,
            "source_index": None,
            "path": {"path": "."},
        }
    elif invalid_state == "dot_required_path":
        data["diagnostic_inputs"]["required_paths"] = [
            {
                "id": "path:.",
                "owner_id": None,
                "source_index": None,
                "path": {"path": "."},
            }
        ]
    elif invalid_state == "unsafe_executable":
        data["diagnostic_inputs"]["tools"][0]["tool"]["name"] = "../python"
    elif invalid_state == "unsafe_service_url":
        data["services"][0]["url"] = "http://user:secret@127.0.0.1:8000"
    elif invalid_state == "unsafe_reference_url":
        data["services"][0]["links"][0]["url"] = "https://user:secret@example.test/docs"
    elif invalid_state == "unsafe_check_url":
        data["checks"][0]["target"] = "http://127.0.0.1:5173?secret=true"
        data["diagnostic_inputs"]["http_checks"][0]["target"] = data["checks"][0]["target"]
    elif invalid_state == "duplicate_service_ids":
        data["services"] = [data["services"][0].copy(), *data["services"]]
    elif invalid_state == "unsorted_service_ids":
        data["services"] = list(reversed(data["services"]))
    elif invalid_state == "invalid_v2_identifier":
        data["services"][0]["id"] = "invalid.id"
    elif invalid_state == "duplicate_environment_names":
        data["environment"] = [data["environment"][0].copy(), *data["environment"]]
    elif invalid_state == "unsorted_environment_names":
        data["environment"] = list(reversed(data["environment"]))
    elif invalid_state == "duplicate_action_ids":
        data["actions"] = [data["actions"][0].copy(), *data["actions"]]
    elif invalid_state == "unsorted_action_ids":
        data["actions"] = list(reversed(data["actions"]))
    elif invalid_state == "duplicate_providers":
        providers = data["services"][0]["providers"]
        data["services"][0]["providers"] = [providers[0].copy(), *providers]
    elif invalid_state == "unsorted_providers":
        data["services"][0]["providers"] = list(reversed(data["services"][0]["providers"]))
    elif invalid_state == "duplicate_link_relations":
        links = data["services"][0]["links"]
        data["services"][0]["links"] = [links[0].copy(), *links]
    elif invalid_state == "unsorted_links":
        data["services"][0]["links"] = list(reversed(data["services"][0]["links"]))
    elif invalid_state == "unsorted_aliases":
        data["environment"][0]["aliases"] = ["z", "a"]
    elif invalid_state == "unsorted_warnings":
        data["warnings"] = [
            {
                "code": "unsafe_path_omitted",
                "message": "Unsafe project path was omitted.",
                "details": {
                    "owner_type": "process",
                    "owner_id": "z",
                    "index": None,
                    "field": "cwd",
                },
            },
            {
                "code": "unsafe_endpoint_omitted",
                "message": "Unsafe endpoint was omitted.",
                "details": {"owner_type": "service", "owner_id": "a", "field": "url"},
            },
        ]
    elif invalid_state == "duplicate_diagnostic_ids":
        tools = data["diagnostic_inputs"]["tools"]
        data["diagnostic_inputs"]["tools"] = [tools[0].copy(), *tools]
    elif invalid_state == "unsorted_diagnostics":
        data["diagnostic_inputs"]["process_cwds"] = list(reversed(data["diagnostic_inputs"]["process_cwds"]))
    elif invalid_state == "http_diagnostic_mismatch":
        data["diagnostic_inputs"]["http_checks"][0]["target"] = "http://127.0.0.1:9999"
    elif invalid_state == "nonpositive_http_attempts":
        data["diagnostic_inputs"]["http_checks"][0]["attempts"] = 0
    elif invalid_state == "dangling_check":
        data["checks"][0]["service_id"] = "missing"
        data["diagnostic_inputs"]["http_checks"][0]["service_id"] = "missing"
    elif invalid_state == "check_reciprocity_mismatch":
        data["services"][0]["check_ids"] = []
    elif invalid_state == "dangling_task_effect":
        data["tasks"][0]["starts"] = ["missing"]
    elif invalid_state == "dangling_dev_provider":
        provider = data["services"][0]["providers"][0]
        provider["id"] = "process:missing"
        provider["process_id"] = "missing"
    elif invalid_state == "dangling_task_provider":
        provider = data["services"][0]["providers"][1]
        provider["id"] = "task:missing"
        provider["task_id"] = "missing"
    elif invalid_state == "noncanonical_action_label":
        data["actions"][0]["label"] = "Start things"
    elif invalid_state == "hidden_service_action":
        data["services"][0]["display"] = "hidden"
    elif invalid_state == "missing_primary":
        for service in data["services"]:
            service["primary"] = False
    elif invalid_state == "metadata_incomplete":
        data["metadata_complete"] = False
    elif invalid_state == "v2_warning":
        data["warnings"] = [
            {
                "code": "unsafe_endpoint_omitted",
                "message": "Unsafe endpoint was omitted.",
                "details": {"owner_type": "service", "owner_id": "api", "field": "url"},
            }
        ]
    else:
        data["project"]["template"] = None

    with pytest.raises(ValidationError):
        NormalizedLifecycleProject.model_validate(data)


def test_exported_root_preserves_duplicate_aliases_and_duplicate_requirement_warnings(tmp_path: Path) -> None:
    project_root = tmp_path / "unsafe-v1"
    project_root.mkdir()
    data = _normalized_unsafe_v1_dump(project_root)
    data["environment"][0]["aliases"] = ["", "", "a"]
    data["diagnostic_inputs"]["environment"][0]["aliases"] = ["", "", "a"]
    duplicate_warning = next(
        warning.copy() for warning in data["warnings"] if warning["code"] == "duplicate_requirement_collapsed"
    )
    data["warnings"] = sorted([*data["warnings"], duplicate_warning], key=_warning_payload_sort_key)

    validated = NormalizedLifecycleProject.model_validate(data)

    assert validated.environment[0].aliases == ("", "", "a")
    duplicate = NormalizationWarning.model_validate(duplicate_warning)
    assert validated.warnings.count(duplicate) == 2
    assert (
        len({
            warning.details["owner_id"] for warning in validated.warnings if warning.code == "unsafe_endpoint_omitted"
        })
        == 2
    )


def test_exported_root_preserves_legacy_v1_nonpositive_http_attempts(tmp_path: Path) -> None:
    spec = LifecycleSpecV1.model_validate({
        "path": tmp_path / ".agentseek" / "lifecycle.toml",
        "version": 1,
        "name": "Legacy Attempts",
        "processes": {"app": {"command": ["python", "app.py"]}},
        "checks": {
            "legacy": {
                "target": "http://127.0.0.1:8000/health",
                "attempts": -1,
            }
        },
    })

    normalized = normalize_lifecycle(spec, project_root=tmp_path)
    validated = NormalizedLifecycleProject.model_validate(normalized.model_dump())

    assert validated.diagnostic_inputs.http_checks[0].attempts == -1


def test_normalize_lifecycle_v2_allows_task_start_stop_overlap_and_extra_process_cwd(tmp_path: Path) -> None:
    spec = LifecycleSpecV2.model_validate(
        {
            "version": 2,
            "template": "example/overlap",
            "name": "Overlap",
            "services": {
                "app": {
                    "name": "Application",
                    "url": "http://127.0.0.1:8000",
                    "kind": "web",
                    "primary": True,
                    "description": "Application.",
                }
            },
            "processes": {
                "app": {"command": ["python", "app.py"], "provides": []},
                "extra": {"command": ["python", "extra.py"], "provides": []},
            },
            "tasks": {
                "restart": {
                    "command": ["python", "restart.py"],
                    "starts": ["app"],
                    "stops": ["app"],
                }
            },
        },
        context={
            "project_root": tmp_path,
            "loader_path": tmp_path / ".agentseek" / "lifecycle.toml",
        },
    )

    normalized = normalize_lifecycle(spec, project_root=tmp_path)

    assert normalized.services[0].providers == (NormalizedProvider(type="task", id="task:restart", task_id="restart"),)
    assert normalized.tasks[0].starts == ("app",)
    assert normalized.tasks[0].stops == ("app",)
    assert tuple(source.owner_id for source in normalized.diagnostic_inputs.process_cwds) == ("app", "extra")
    assert NormalizedLifecycleProject.model_validate(normalized.model_dump()) == normalized


def test_exported_root_round_trips_real_normalized_v1_v2_and_unsafe_v1(tmp_path: Path) -> None:
    safe_v1 = NormalizedLifecycleProject.model_validate(_normalized_v1_dump(tmp_path))
    assert NormalizedLifecycleProject.model_validate(safe_v1.model_dump()) == safe_v1

    v2_root = tmp_path / "v2"
    v2_root.mkdir()
    v2 = normalize_lifecycle(_normalized_v2_projection_fixture(v2_root), project_root=v2_root)
    assert NormalizedLifecycleProject.model_validate(v2.model_dump()) == v2

    unsafe_root = tmp_path / "unsafe-v1"
    unsafe_root.mkdir()
    (unsafe_root / "symlink-out").symlink_to(tmp_path / "outside", target_is_directory=True)
    unsafe_spec = LifecycleSpecV1.model_validate({
        **tomllib.loads((FIXTURES / "v1-unsafe-projection.toml").read_text(encoding="utf-8")),
        "path": unsafe_root / ".agentseek" / "lifecycle.toml",
    })
    unsafe_v1 = normalize_lifecycle(unsafe_spec, project_root=unsafe_root)
    assert NormalizedLifecycleProject.model_validate(unsafe_v1.model_dump()) == unsafe_v1
