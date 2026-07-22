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

from agentseek.cli.lifecycle.authored import LifecycleSpecV1
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
)
from agentseek.cli.lifecycle.normalize import normalize_lifecycle

FIXTURES = Path(__file__).parent.parent / "fixtures" / "lifecycle"


class _ExternalStateAccessed(AssertionError):
    pass


@pytest.mark.parametrize(
    ("model", "fields"),
    [
        (SafeModel, ()),
        (NormalizedProjectFile, ("path", "rel")),
        (NormalizedProject, ("template", "name", "description", "guide")),
        (NormalizedEnvironmentRequirement, ("name", "required", "description", "aliases")),
        (NormalizedProvider, ("type", "id", "process_id", "task_id")),
        (NormalizedReference, ("rel", "url")),
        (NormalizedService, ("id", "name", "description", "url", "kind", "display", "primary", "tech", "providers", "check_ids", "links")),
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
        (NormalizedLifecycleProject, ("lifecycle_version", "project", "metadata_complete", "environment", "services", "checks", "tasks", "actions", "warnings", "diagnostic_inputs")),
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
    assert NormalizedService(id="web", name=None, description=None, url=None, kind=None, display=None, primary=None, tech=None).providers == ()
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
        {"id": "service:web:copy", "type": "copy_endpoint", "label": "Copy", "service_id": "web", "url": "http://127.0.0.1"},
        {"id": "service:web:reference:docs", "type": "open_reference", "label": "Docs", "service_id": "web", "url": "https://example.test/docs", "reference_rel": "docs"},
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
        {"id": "service:web:open", "type": "copy_endpoint", "label": "Copy", "service_id": "web", "url": "http://127.0.0.1"},
        {"id": "service:web:reference:docs", "type": "open_reference", "label": "Docs", "service_id": "web", "url": "http://127.0.0.1"},
        {"id": "project:start_dev", "type": "start_dev", "label": "Start", "task_id": "stack"},
        {"id": "task:stack", "type": "run_task", "label": "Run"},
    ],
)
def test_model_shape_action_rejects_noncanonical_relationship(action: dict[str, str]) -> None:
    with pytest.raises(ValidationError):
        NormalizedAction.model_validate(action)


def test_model_shape_http_diagnostic_id_is_canonical() -> None:
    source = HttpDiagnosticSource(id="service-check:api", service_id="api", target="http://127.0.0.1", timeout=1.0, attempts=1)

    assert source.id == "service-check:api"
    with pytest.raises(ValidationError):
        HttpDiagnosticSource(id="api", service_id="api", target="http://127.0.0.1", timeout=1.0, attempts=1)
    with pytest.raises(ValidationError):
        HttpDiagnosticSource(id="service-check:", service_id="api", target="http://127.0.0.1", timeout=1.0, attempts=1)


@pytest.mark.parametrize(
    ("code", "details", "message"),
    [
        ("lifecycle_v1_metadata_incomplete", {}, "Lifecycle v1 metadata is incomplete."),
        ("unsafe_endpoint_omitted", {"owner_type": "service", "owner_id": "app", "field": "url"}, "Unsafe endpoint was omitted."),
        ("unsafe_path_omitted", {"owner_type": "process", "owner_id": "app", "index": 0, "field": "cwd"}, "Unsafe project path was omitted."),
        ("duplicate_requirement_collapsed", {"requirement_type": "tool", "first_index": 0, "duplicate_index": 1}, "Duplicate requirement was collapsed."),
    ],
)
def test_model_shape_warning_has_fixed_message_and_copied_ordered_details(code: str, details: dict[str, str | int], message: str) -> None:
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
        ("unsafe_endpoint_omitted", "Unsafe endpoint was omitted.", {"owner_id": "app", "owner_type": "service", "field": "url"}),
        ("unsafe_path_omitted", "Unsafe project path was omitted.", {"owner_type": "process", "owner_id": "app", "field": "cwd"}),
        ("duplicate_requirement_collapsed", "Duplicate requirement was collapsed.", {"requirement_type": "tool", "first_index": 0, "duplicate_index": 1, "extra": None}),
    ],
)
def test_model_shape_warning_rejects_noncanonical_message_or_details(code: str, message: str, details: dict[str, str | int | None]) -> None:
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
    spec = LifecycleSpecV1.model_validate(
        {
            "path": tmp_path / ".agentseek" / "lifecycle.toml",
            "version": 1,
            "name": "Example",
            "processes": {"app": {"command": ["python", "never-retain-this-command"]}},
        }
    )

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
    spec = LifecycleSpecV1.model_validate(
        {
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
        }
    )

    normalized = normalize_lifecycle(spec, project_root=tmp_path)

    assert normalized.environment == (
        NormalizedEnvironmentRequirement(name="A_KEY", required=False, description=None, aliases=("A_ALIAS", "B_ALIAS")),
        NormalizedEnvironmentRequirement(name="Z_KEY", required=True, description="Z description", aliases=("A_ALIAS", "Z_ALIAS")),
    )
    assert normalized.services == (
        NormalizedService(id="api", name=None, description=None, url="http://127.0.0.1:8000", kind=None, display=None, primary=None, tech=None),
        NormalizedService(id="web", name=None, description=None, url="http://127.0.0.1:3000", kind=None, display=None, primary=None, tech=None),
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
            EnvironmentDiagnosticSource(id="env:A_KEY", name="A_KEY", aliases=("A_ALIAS", "B_ALIAS"), required=False, has_usable_default=False),
            EnvironmentDiagnosticSource(id="env:Z_KEY", name="Z_KEY", aliases=("A_ALIAS", "Z_ALIAS"), required=True, has_usable_default=True),
        ),
        http_checks=(
            HttpDiagnosticSource(id="service-check:probe", service_id=None, target="http://127.0.0.1:8000/health", timeout=2.5, attempts=3),
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
    spec = LifecycleSpecV1.model_validate(
        {
            **tomllib.loads((FIXTURES / "v1-unsafe-projection.toml").read_text(encoding="utf-8")),
            "path": project_root / ".agentseek" / "lifecycle.toml",
        }
    )

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
        NormalizedService(id="api", name=None, description=None, url=None, kind=None, display=None, primary=None, tech=None),
    )
    assert normalized.checks == (
        NormalizedCheckDefinition(id="probe", service_id=None, target=None),
    )
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
        environment=(
            EnvironmentDiagnosticSource(id="env:API_KEY", name="API_KEY", has_usable_default=True),
        ),
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
    assert tuple(sorted(normalized.warnings, key=lambda warning: (warning.code, warning.message, json.dumps(warning.details, separators=(",", ":"))))) == expected_warnings

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
