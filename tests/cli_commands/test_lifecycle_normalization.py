from __future__ import annotations

import json
import shutil
import socket
import subprocess
import tomllib
import urllib.request
from collections.abc import Mapping
from pathlib import Path

import pytest
from pydantic import ValidationError

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
        (DiagnosticInputs, ("env_file", "tools", "required_paths", "process_cwds", "environment", "http_checks")),
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
    project = NormalizedLifecycleProject(
        lifecycle_version=2,
        project=NormalizedProject(template=None, name="Example", description=None, guide=None),
        metadata_complete=True,
    )

    assert project.environment == ()
    assert project.services == ()
    assert project.checks == ()
    assert project.tasks == ()
    assert project.actions == ()
    assert project.warnings == ()
    assert project.diagnostic_inputs == DiagnosticInputs()
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
            {"owner_type": "process", "owner_id": "app", "index": 0, "field": "cwd"},
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
    assert "changed" not in warning.details


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
                key=lambda warning: (warning.code, warning.message, json.dumps(warning.details, separators=(",", ":"))),
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
