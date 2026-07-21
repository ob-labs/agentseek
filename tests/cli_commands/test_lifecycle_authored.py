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
    SUPPORTED_LIFECYCLE_VERSION,
    SUPPORTED_LIFECYCLE_VERSIONS,
    AuthoredLifecycleSpec,
    Check,
    CheckV1,
    CheckV2,
    LifecycleSpec,
    LifecycleSpecV1,
    LifecycleSpecV2,
    Process,
    ProcessV1,
    Service,
    ServiceV1,
    ServiceV2,
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
    ("fixture", "service_count"),
    [
        ("v2-service-free.toml", 0),
        ("v2-same-id.toml", 1),
        ("v2-bub-explicit.toml", 3),
        ("v2-task-providers.toml", 2),
    ],
)
def test_loads_valid_v2_fixture_with_authored_literals(fixture: str, service_count: int) -> None:
    path = FIXTURES / fixture

    spec = read_lifecycle_spec(path, project_root=FIXTURES)

    assert isinstance(spec, LifecycleSpecV2)
    assert spec.version == 2
    assert len(spec.services) == service_count
    assert spec.template == path.read_text(encoding="utf-8").split('template = "')[1].split('"', 1)[0]
    assert spec.name


def test_v2_distinguishes_absent_and_explicit_process_provides() -> None:
    same_id = read_lifecycle_spec(FIXTURES / "v2-same-id.toml", project_root=FIXTURES)
    service_free = read_lifecycle_spec(FIXTURES / "v2-service-free.toml", project_root=FIXTURES)
    explicit = read_lifecycle_spec(FIXTURES / "v2-bub-explicit.toml", project_root=FIXTURES)

    assert isinstance(same_id, LifecycleSpecV2)
    assert same_id.processes["app"].provides is None
    assert isinstance(service_free, LifecycleSpecV2)
    assert service_free.processes["worker"].provides == ()
    assert explicit.processes["frontend"].provides == ("app", "copilotkit")


def test_v2_constants_and_public_exports_are_versioned_and_typed() -> None:
    from agentseek.cli.lifecycle import SUPPORTED_LIFECYCLE_VERSION as package_version
    from agentseek.cli.lifecycle import SUPPORTED_LIFECYCLE_VERSIONS as package_versions
    from agentseek.cli.lifecycle import AuthoredLifecycleSpec as package_spec

    assert SUPPORTED_LIFECYCLE_VERSIONS == (1, 2)
    assert SUPPORTED_LIFECYCLE_VERSION == 2
    assert package_versions == (1, 2)
    assert package_version == 2
    assert package_spec is AuthoredLifecycleSpec


def test_v2_preserves_service_literals_and_task_effects() -> None:
    explicit = read_lifecycle_spec(FIXTURES / "v2-bub-explicit.toml", project_root=FIXTURES)
    tasks = read_lifecycle_spec(FIXTURES / "v2-task-providers.toml", project_root=FIXTURES)

    assert isinstance(explicit, LifecycleSpecV2)
    assert explicit.services["gateway"].url == "http://127.0.0.1:8088/agent"
    assert explicit.services["gateway"].links.model_dump(exclude_none=True) == {"docs": "https://docs.ag-ui.com/introduction"}
    assert isinstance(tasks, LifecycleSpecV2)
    assert tasks.tasks["stack"].starts == ("app", "database")
    assert tasks.tasks["stack-stop"].stops == ("app", "database")


def test_v2_models_expose_exhaustive_defaults_and_immutable_authored_fields(tmp_path: Path) -> None:
    spec = LifecycleSpecV2.model_validate(
        {
            "version": 2,
            "template": "example/defaults",
            "name": "Defaults",
            "services": {
                "app": {
                    "name": "Application",
                    "kind": "web",
                    "url": "http://127.0.0.1:8000",
                    "primary": True,
                    "description": "Application service.",
                }
            },
            "processes": {"app": {"command": ["python", "app.py"]}},
            "checks": {"app": {"target": "http://127.0.0.1:8000"}},
            "tasks": {"build": {"command": ["python", "build.py"]}},
        },
        context={"project_root": tmp_path, "loader_path": tmp_path / "lifecycle.toml"},
    )

    assert spec.path == tmp_path / "lifecycle.toml"
    assert spec.description is None and spec.env_file is None and spec.guide is None
    assert spec.tools.required == () and spec.paths.required == () and spec.env == {}
    assert spec.services["app"].display == "default" and spec.services["app"].tech is None
    assert spec.services["app"].links.model_dump(exclude_none=True) == {}
    assert spec.processes["app"].cwd == "." and spec.processes["app"].provides is None
    assert spec.checks["app"].type == "http" and spec.checks["app"].timeout == 2.0 and spec.checks["app"].attempts == 1
    assert spec.checks["app"].service is None
    assert spec.tasks["build"].cwd == "." and spec.tasks["build"].description == ""
    assert spec.tasks["build"].starts == () and spec.tasks["build"].stops == ()
    with pytest.raises(ValidationError):
        spec.name = "Changed"


@pytest.mark.parametrize(
    ("surface", "kind", "rel", "value", "error_type"),
    [
        ("service", "web", None, "${SERVICE_URL}", "unresolved_placeholder"),
        ("service", "web", None, "relative/path", "url_absolute_required"),
        ("service", "web", None, "http://", "url_host_required"),
        ("service", "web", None, "http://service.test:invalid", "url_host_required"),
        ("service", "web", None, "ftp://service.test", "url_scheme_invalid"),
        ("service", "web", None, "http://user@service.test", "url_userinfo_forbidden"),
        ("service", "web", None, "http://service.test?", "url_query_forbidden"),
        ("service", "web", None, "http://service.test#", "url_fragment_forbidden"),
        ("service", "web", None, "http://{control}service.test", "url_control_forbidden"),
        ("check", None, None, "ws://service.test", "url_scheme_invalid"),
        ("check", None, None, "http://service.test:65536", "url_host_required"),
        ("reference", "web", "docs", "${DOCS_URL}", "unresolved_placeholder"),
        ("reference", "web", "docs", "https://", "reference_host_invalid"),
        ("reference", "web", "docs", "http://docs.test", "url_scheme_invalid"),
        ("reference", "web", "docs", "https://user@docs.test", "url_userinfo_forbidden"),
        ("reference", "web", "docs", "https://docs.test?", "url_query_forbidden"),
        ("reference", "web", "docs", "https://docs.test#", "url_fragment_forbidden"),
        ("reference", "web", "api_docs", "http://public.test/openapi", "reference_host_invalid"),
        ("reference", "web", "studio", "https://studio.test/?view=graph", "reference_query_invalid"),
        ("reference", "web", "studio", "https://studio.test/?baseUrl=https%3A%2F%2Fapi.test%3Ftoken%3Dsecret", "reference_query_invalid"),
    ],
)
def test_v2_authored_models_translate_every_url_safety_category(
    surface: str, kind: str | None, rel: str | None, value: str, error_type: str
) -> None:
    value = value.replace("{control}", chr(31))
    if surface == "check":
        model = CheckV2.model_validate
        data = {"target": value}
    else:
        data = {
            "name": "Service",
            "kind": kind,
            "url": "http://service.test",
            "description": "Service description.",
        }
        if surface == "service":
            data["url"] = value
        else:
            data["links"] = {rel: value}
        model = ServiceV2.model_validate

    with pytest.raises(ValidationError) as exc_info:
        model(data)

    assert exc_info.value.errors()[0]["type"] == error_type


@pytest.mark.parametrize(
    ("original", "revised", "path", "code"),
    [
        ('template = "bub/default"', 'template = "   "', "template", "value_blank"),
        ('name = "Bub Agent"', 'name = "   "', "name", "value_blank"),
        ('name = "Application"', 'name = "   "', "services.app.name", "value_blank"),
        ('description = "Browser application for this template."', 'description = "   "', "services.app.description", "value_blank"),
        ('primary = true', 'primary = false', "$", "primary_required"),
        ('display = "default"', 'display = "hidden"', "$", "primary_hidden"),
        ('command = ["npm", "run", "dev"]', 'command = []', "processes.frontend.command", "command_empty"),
        ('target = "http://127.0.0.1:5173"', 'target = "http://127.0.0.1:5173"\nattempts = 0', "checks.frontend.attempts", "number_not_positive"),
        ('provides = ["app", "copilotkit"]', 'provides = ["missing"]', "$", "service_reference_unknown"),
        ('service = "app"', 'service = "missing"', "$", "service_reference_unknown"),
        ('command = ["python", "gateway.py"]', 'command = ["python", "gateway.py"]\nprovides = ["missing"]', "$", "service_reference_unknown"),
        ('provides = ["app", "copilotkit"]', 'provides = ["missing"]', "$", "service_reference_unknown"),
        ('guide = "README.md"', 'guide = "../README.md"', "guide", "path_unsafe"),
        ('url = "http://127.0.0.1:5173"', 'url = "${APP_URL}"', "services.app.url", "placeholder_unresolved"),
        ('url = "http://127.0.0.1:5173"', 'url = "/relative"', "services.app.url", "url_invalid"),
        ('url = "http://127.0.0.1:5173"', 'url = "ftp://127.0.0.1"', "services.app.url", "url_scheme_invalid"),
        ('url = "http://127.0.0.1:5173"', 'url = "http://user@127.0.0.1:5173"', "services.app.url", "url_component_forbidden"),
        ('url = "http://127.0.0.1:5173"', 'url = "http://127.0.0.1:5173?token=secret"', "services.app.url", "url_component_forbidden"),
        ('url = "http://127.0.0.1:5173"', 'url = "http://127.0.0.1:5173#fragment"', "services.app.url", "url_component_forbidden"),
    ],
)
def test_v2_invalid_authored_values_have_owned_issue_paths(
    tmp_path: Path, original: str, revised: str, path: str, code: str
) -> None:
    source = (FIXTURES / "v2-bub-explicit.toml").read_text(encoding="utf-8")
    lifecycle = tmp_path / "lifecycle.toml"
    lifecycle.write_text(source.replace(original, revised, 1), encoding="utf-8")

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(lifecycle, project_root=tmp_path)

    assert LifecycleValidationIssue(path, code, _message_for_code(code)) in exc_info.value.issues


@pytest.mark.parametrize(
    ("original", "revised", "path", "code"),
    [
        ('required = ["python"]', 'required = ["python", "python"]', "tools.required", "requirement_duplicate"),
        ('required = ["python"]', 'required = ["../python"]', "tools.required", "tool_invalid"),
        ('required = ["pyproject.toml"]', 'required = ["pyproject.toml", "pyproject.toml"]', "paths.required", "requirement_duplicate"),
        ('required = ["pyproject.toml"]', 'required = ["../pyproject.toml"]', "paths.required", "path_unsafe"),
        ('cwd = "."', 'cwd = "../outside"', "processes.worker.cwd", "path_unsafe"),
        ('cwd = "tasks"', 'cwd = "../outside"', "tasks.seed.cwd", "path_unsafe"),
        ('starts = ["app", "database"]', 'starts = ["missing"]', "$", "service_reference_unknown"),
        ('stops = ["app", "database"]', 'stops = ["missing"]', "$", "service_reference_unknown"),
    ],
)
def test_v2_rejects_unsafe_requirements_paths_and_task_relationships(
    tmp_path: Path, original: str, revised: str, path: str, code: str
) -> None:
    fixture = "v2-task-providers.toml" if "starts" in revised or "stops" in revised else "v2-service-free.toml"
    source = (FIXTURES / fixture).read_text(encoding="utf-8")
    lifecycle = tmp_path / "lifecycle.toml"
    lifecycle.write_text(source.replace(original, revised, 1), encoding="utf-8")

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(lifecycle, project_root=tmp_path)

    assert LifecycleValidationIssue(path, code, _message_for_code(code)) in exc_info.value.issues


@pytest.mark.parametrize(
    ("original", "revised", "path", "code"),
    [
        ('url = "http://127.0.0.1:5173"', 'url = "http://"', "services.app.url", "url_invalid"),
        ('url = "http://127.0.0.1:5173"', 'url = "http://\\u001f127.0.0.1"', "services.app.url", "url_component_forbidden"),
        ('docs = "https://docs.ag-ui.com/introduction"', 'docs = "https://"', "services.gateway.links.docs", "url_invalid"),
        ('docs = "https://docs.ag-ui.com/introduction"', 'docs = "http://docs.ag-ui.com"', "services.gateway.links.docs", "url_scheme_invalid"),
        ('docs = "https://docs.ag-ui.com/introduction"', 'docs = "https://docs.ag-ui.com?token=secret"', "services.gateway.links.docs", "url_component_forbidden"),
        ('docs = "https://docs.ag-ui.com/introduction"', 'docs = "https://docs.ag-ui.com#fragment"', "services.gateway.links.docs", "url_component_forbidden"),
        ('docs = "https://docs.ag-ui.com/introduction"', 'docs = "https://user@docs.ag-ui.com"', "services.gateway.links.docs", "url_component_forbidden"),
        ('docs = "https://docs.ag-ui.com/introduction"', 'docs = "${DOCS_URL}"', "services.gateway.links.docs", "placeholder_unresolved"),
        ('docs = "https://docs.ag-ui.com/introduction"', 'studio = "https://studio.test/?view=graph"', "services.gateway.links.studio", "reference_query_invalid"),
    ],
)
def test_v2_url_and_reference_failures_use_exact_owned_errors(
    tmp_path: Path, original: str, revised: str, path: str, code: str
) -> None:
    source = (FIXTURES / "v2-bub-explicit.toml").read_text(encoding="utf-8")
    lifecycle = tmp_path / "lifecycle.toml"
    lifecycle.write_text(source.replace(original, revised, 1), encoding="utf-8")

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(lifecycle, project_root=tmp_path)

    assert LifecycleValidationIssue(path, code, _message_for_code(code)) in exc_info.value.issues


def test_v2_rejects_multiple_primary_services_and_missing_check_association(tmp_path: Path) -> None:
    source = (FIXTURES / "v2-bub-explicit.toml").read_text(encoding="utf-8")
    lifecycle = tmp_path / "lifecycle.toml"
    lifecycle.write_text(
        source.replace('display = "advanced"', 'display = "advanced"\nprimary = true').replace(
            '[checks.gateway]\ntarget = "http://127.0.0.1:8088/health"',
            '[checks.orphan]\ntarget = "http://127.0.0.1:8088/health"',
        ),
        encoding="utf-8",
    )

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(lifecycle, project_root=tmp_path)

    assert LifecycleValidationIssue("$", "primary_multiple", "Only one primary service is allowed.") in exc_info.value.issues

    lifecycle.write_text(
        source.replace(
            '[checks.gateway]\ntarget = "http://127.0.0.1:8088/health"',
            '[checks.orphan]\ntarget = "http://127.0.0.1:8088/health"',
        ),
        encoding="utf-8",
    )
    with pytest.raises(LifecycleValidationError) as missing_service:
        read_lifecycle_spec(lifecycle, project_root=tmp_path)
    assert LifecycleValidationIssue("$", "check_service_missing", "Check must be associated with a service.") in missing_service.value.issues


def test_v2_rejects_invalid_map_identifier_at_the_exact_safe_path(tmp_path: Path) -> None:
    source = (FIXTURES / "v2-same-id.toml").read_text(encoding="utf-8")
    lifecycle = tmp_path / "lifecycle.toml"
    lifecycle.write_text(source.replace("[services.app]", '[services."bad.id"]'), encoding="utf-8")

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(lifecycle, project_root=tmp_path)

    assert LifecycleValidationIssue(
        "services.<invalid-id>.<invalid-id>", "identifier_invalid", "Identifier has an invalid format."
    ) in exc_info.value.issues


@pytest.mark.parametrize(
    ("fixture", "original", "revised", "path"),
    [
        ("v2-same-id.toml", "[services.app]", '[services."bad.id"]', "services.<invalid-id>.<invalid-id>"),
        ("v2-same-id.toml", "[processes.app]", '[processes."bad.id"]', "processes.<invalid-id>.<invalid-id>"),
        ("v2-same-id.toml", "[checks.app]", '[checks."bad.id"]', "checks.<invalid-id>.<invalid-id>"),
        ("v2-task-providers.toml", "[tasks.stack]", '[tasks."bad.id"]', "tasks.<invalid-id>.<invalid-id>"),
        ("v2-service-free.toml", "[env.API_KEY]", '[env."bad.id"]', "env.<invalid-id>.<invalid-id>"),
    ],
)
def test_v2_rejects_invalid_keys_under_every_authored_map(
    tmp_path: Path, fixture: str, original: str, revised: str, path: str
) -> None:
    lifecycle = tmp_path / "lifecycle.toml"
    lifecycle.write_text((FIXTURES / fixture).read_text(encoding="utf-8").replace(original, revised), encoding="utf-8")

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(lifecycle, project_root=tmp_path)

    assert LifecycleValidationIssue(path, "identifier_invalid", "Identifier has an invalid format.") in exc_info.value.issues


def test_v2_rejects_authored_loader_path_but_v1_keeps_its_ignored_override(tmp_path: Path) -> None:
    v2 = tmp_path / "v2.toml"
    v2.write_text(
        (FIXTURES / "v2-same-id.toml").read_text(encoding="utf-8").replace('name = "Same Identifier Project"', 'path = "authored.toml"\nname = "Same Identifier Project"'),
        encoding="utf-8",
    )
    with pytest.raises(LifecycleValidationError) as v2_error:
        read_lifecycle_spec(v2, project_root=tmp_path)
    assert LifecycleValidationIssue("path", "field_forbidden", "Field is not allowed.") in v2_error.value.issues

    v1 = tmp_path / "v1.toml"
    v1.write_text(_coercible_text().replace('name = "Coercible Project"', 'path = "authored.toml"\nname = "Coercible Project"'), encoding="utf-8")
    loaded_v1 = read_lifecycle_spec(v1, project_root=tmp_path)
    assert loaded_v1.path == v1


@pytest.mark.parametrize(
    ("field", "safe_path"),
    [("path", "path"), ("_loader_path", "<invalid-id>"), ("__loader_path", "<invalid-id>")],
)
def test_v2_rejects_authored_loader_fields_without_overriding_loader_path(
    tmp_path: Path, field: str, safe_path: str
) -> None:
    lifecycle = tmp_path / "lifecycle.toml"
    lifecycle.write_text(
        (FIXTURES / "v2-same-id.toml").read_text(encoding="utf-8").replace(
            'name = "Same Identifier Project"', f'{field} = "authored.toml"\nname = "Same Identifier Project"'
        ),
        encoding="utf-8",
    )

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(lifecycle, project_root=tmp_path)

    assert LifecycleValidationIssue(safe_path, "field_forbidden", "Field is not allowed.") in exc_info.value.issues


@pytest.mark.parametrize(
    ("version", "model"),
    [("\"2\"", LifecycleSpecV2), ("2.0", LifecycleSpecV2), ("\"1\"", LifecycleSpecV1), ("1.0", LifecycleSpecV1), ("true", LifecycleSpecV1)],
)
def test_version_probe_coerces_before_selecting_the_authored_model(tmp_path: Path, version: str, model: type[object]) -> None:
    source = (FIXTURES / ("v2-same-id.toml" if model is LifecycleSpecV2 else "v1-coercible.toml")).read_text(encoding="utf-8")
    path = tmp_path / "lifecycle.toml"
    path.write_text(source.replace('version = 2' if model is LifecycleSpecV2 else 'version = "1"', f"version = {version}"), encoding="utf-8")

    assert isinstance(read_lifecycle_spec(path, project_root=tmp_path), model)


def test_version_probe_reports_false_as_coerced_unsupported_version(tmp_path: Path) -> None:
    path = tmp_path / "lifecycle.toml"
    path.write_text('version = false\nname = "Project"\n[processes.app]\ncommand = ["python"]\n', encoding="utf-8")

    with pytest.raises(LifecycleVersionUnsupportedError) as exc_info:
        read_lifecycle_spec(path, project_root=tmp_path)

    assert exc_info.value.found == 0
    assert exc_info.value.supported == (1, 2)


@pytest.mark.parametrize("version", [None, '"two"'])
def test_version_probe_reports_missing_or_unparseable_versions_as_unknown(tmp_path: Path, version: str | None) -> None:
    path = tmp_path / "lifecycle.toml"
    declaration = "" if version is None else f"version = {version}\n"
    path.write_text(f'{declaration}name = "Project"\n[processes.app]\ncommand = ["python"]\n', encoding="utf-8")

    with pytest.raises(LifecycleVersionUnsupportedError) as exc_info:
        read_lifecycle_spec(path, project_root=tmp_path)

    assert exc_info.value.found is None
    assert exc_info.value.supported == (1, 2)


@pytest.mark.parametrize(
    ("fixture", "original_version", "version", "authored_name", "expected_version"),
    [
        ("v2-same-id.toml", "version = 2", '"2"', 'name = "Same Identifier Project"', 2),
        ("v2-same-id.toml", "version = 2", "2.0", 'name = "Same Identifier Project"', 2),
        ("v1-coercible.toml", 'version = "1"', '"1"', 'name = "Coercible Project"', 1),
    ],
)
def test_selected_model_errors_report_the_coerced_version(
    tmp_path: Path, fixture: str, original_version: str, version: str, authored_name: str, expected_version: int
) -> None:
    path = tmp_path / "lifecycle.toml"
    path.write_text(
        (FIXTURES / fixture).read_text(encoding="utf-8").replace(original_version, f"version = {version}").replace(authored_name, 'name = ""'),
        encoding="utf-8",
    )

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(path, project_root=tmp_path)

    assert exc_info.value.lifecycle_version == expected_version
    assert any(issue.code == "value_blank" and issue.message == "Value must not be blank." for issue in exc_info.value.issues)


def test_v2_allows_an_empty_optional_root_description(tmp_path: Path) -> None:
    path = tmp_path / "lifecycle.toml"
    path.write_text(
        (FIXTURES / "v2-same-id.toml").read_text(encoding="utf-8").replace(
            'description = "Uses the same identifier relationship convention."', 'description = ""'
        ),
        encoding="utf-8",
    )

    assert read_lifecycle_spec(path, project_root=tmp_path).description == ""


@pytest.mark.parametrize(
    ("original", "revised", "path"),
    [
        ('provides = ["app", "copilotkit"]', 'provides = ["bad.id"]', "processes.frontend.provides[0]"),
        ('service = "app"', 'service = "bad.id"', "checks.frontend.service"),
        ('starts = ["app", "database"]', 'starts = ["bad.id"]', "tasks.stack.starts[0]"),
        ('stops = ["app", "database"]', 'stops = ["bad.id"]', "tasks.stack-stop.stops[0]"),
    ],
)
def test_v2_rejects_malformed_relationship_identifiers_before_unknown_reference(
    tmp_path: Path, original: str, revised: str, path: str
) -> None:
    fixture = "v2-bub-explicit.toml" if "processes.frontend" in path or "checks.frontend" in path else "v2-task-providers.toml"
    lifecycle = tmp_path / "lifecycle.toml"
    lifecycle.write_text((FIXTURES / fixture).read_text(encoding="utf-8").replace(original, revised, 1), encoding="utf-8")

    with pytest.raises(LifecycleValidationError) as exc_info:
        read_lifecycle_spec(lifecycle, project_root=tmp_path)

    assert LifecycleValidationIssue(path, "identifier_invalid", "Identifier has an invalid format.") in exc_info.value.issues


def _message_for_code(code: str) -> str:
    return {
        "value_blank": "Value must not be blank.",
        "primary_required": "Exactly one primary service is required.",
        "primary_hidden": "Primary service must not be hidden.",
        "command_empty": "Command must not be empty.",
        "number_not_positive": "Value must be greater than zero.",
        "service_reference_unknown": "Referenced service does not exist.",
        "path_unsafe": "Project path is unsafe.",
        "placeholder_unresolved": "Value contains an unresolved placeholder.",
        "url_invalid": "URL is invalid.",
        "url_scheme_invalid": "URL scheme is not allowed.",
        "url_component_forbidden": "URL contains a forbidden component.",
        "requirement_duplicate": "Requirement is duplicated.",
        "tool_invalid": "Required tool is not a safe executable name.",
        "reference_query_invalid": "Reference query is not allowed.",
    }[code]


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
