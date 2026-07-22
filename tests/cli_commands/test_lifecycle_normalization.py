from __future__ import annotations

from collections.abc import Mapping

import pytest
from pydantic import ValidationError

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
