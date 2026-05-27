from __future__ import annotations

from pathlib import Path

import yaml
from agentseek_cli.app import build_app
from agentseek_cli.commands.deploy import (
    _COMPOSE_TEMPLATE,
    DeployContext,
    DeployMode,
    _plan_files,
    _render_compose,
    _render_k8s_deployment,
    _render_k8s_service,
    _resolve_image,
    _resolve_slug,
)
from typer.testing import CliRunner


def _ctx(**overrides: object) -> DeployContext:
    base: dict[str, object] = {
        "slug": "demo",
        "image": "demo:latest",
        "port": 8000,
        "replicas": 1,
        "namespace": "default",
    }
    base.update(overrides)
    return DeployContext(**base)  # type: ignore[arg-type]


def test_no_dry_run_exits_2() -> None:
    result = CliRunner().invoke(build_app(), ["deploy", "--mode", "docker-compose"])
    assert result.exit_code == 2
    assert "--dry-run" in result.stderr


def test_dry_run_compose_writes_compose_yaml(tmp_path: Path) -> None:
    out = tmp_path / "deploy"
    result = CliRunner().invoke(
        build_app(),
        [
            "deploy",
            "--dry-run",
            "--mode",
            "docker-compose",
            "--output",
            str(out),
            "--image",
            "demo:1.0",
            "--slug",
            "demo",
            "--port",
            "9000",
        ],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    compose = out / "docker-compose.yaml"
    assert compose.exists()
    not_k8s = list((out / "k8s").glob("*")) if (out / "k8s").exists() else []
    assert not_k8s == []
    parsed = yaml.safe_load(compose.read_text())
    assert "demo" in parsed["services"]
    assert parsed["services"]["demo"]["image"] == "demo:1.0"
    assert parsed["services"]["demo"]["ports"] == ["9000:9000"]


def test_dry_run_k8s_writes_two_yamls(tmp_path: Path) -> None:
    out = tmp_path / "deploy"
    result = CliRunner().invoke(
        build_app(),
        ["deploy", "--dry-run", "--mode", "k8s", "--output", str(out), "--slug", "demo"],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    deployment = out / "k8s" / "deployment.yaml"
    service = out / "k8s" / "service.yaml"
    assert deployment.exists()
    assert service.exists()
    assert not (out / "docker-compose.yaml").exists()
    parsed = yaml.safe_load(deployment.read_text())
    assert parsed["kind"] == "Deployment"
    assert parsed["metadata"]["name"] == "demo"


def test_dry_run_both_writes_three_files(tmp_path: Path) -> None:
    out = tmp_path / "deploy"
    result = CliRunner().invoke(
        build_app(),
        ["deploy", "--dry-run", "--mode", "both", "--output", str(out), "--slug", "demo"],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    assert (out / "docker-compose.yaml").exists()
    assert (out / "k8s" / "deployment.yaml").exists()
    assert (out / "k8s" / "service.yaml").exists()


def test_replicas_appears_in_deployment(tmp_path: Path) -> None:
    out = tmp_path / "deploy"
    CliRunner().invoke(
        build_app(),
        [
            "deploy",
            "--dry-run",
            "--mode",
            "k8s",
            "--output",
            str(out),
            "--slug",
            "demo",
            "--replicas",
            "5",
        ],
    )
    parsed = yaml.safe_load((out / "k8s" / "deployment.yaml").read_text())
    assert parsed["spec"]["replicas"] == 5


def test_namespace_in_service(tmp_path: Path) -> None:
    out = tmp_path / "deploy"
    CliRunner().invoke(
        build_app(),
        [
            "deploy",
            "--dry-run",
            "--mode",
            "k8s",
            "--output",
            str(out),
            "--slug",
            "demo",
            "--namespace",
            "platform",
        ],
    )
    parsed = yaml.safe_load((out / "k8s" / "service.yaml").read_text())
    assert parsed["metadata"]["namespace"] == "platform"


def test_slug_inferred_from_cwd(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "My Cool App"
    project.mkdir()
    monkeypatch.chdir(project)
    out = tmp_path / "deploy"
    result = CliRunner().invoke(
        build_app(),
        ["deploy", "--dry-run", "--mode", "docker-compose", "--output", str(out)],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    parsed = yaml.safe_load((out / "docker-compose.yaml").read_text())
    # spaces / case folded into a docker-friendly slug
    services = list(parsed["services"].keys())
    assert services == ["my-cool-app"]
    assert parsed["services"]["my-cool-app"]["image"] == "my-cool-app:latest"


# Direct unit tests on internal helpers for tighter coverage.


def test_resolve_slug_uses_override() -> None:
    assert _resolve_slug(Path("/tmp/whatever"), "Override Name") == "override-name"  # noqa: S108


def test_resolve_image_defaults_to_latest() -> None:
    assert _resolve_image("demo", None) == "demo:latest"
    assert _resolve_image("demo", "registry.example.com/demo:rc1") == "registry.example.com/demo:rc1"


def test_plan_files_both_yields_three_paths(tmp_path: Path) -> None:
    files = _plan_files(DeployMode.BOTH, _ctx(), tmp_path)
    assert set(files.keys()) == {
        tmp_path / "docker-compose.yaml",
        tmp_path / "k8s" / "deployment.yaml",
        tmp_path / "k8s" / "service.yaml",
    }


def test_compose_template_uses_keep_trailing_newline() -> None:
    rendered = _render_compose(_ctx())
    assert rendered.endswith("\n")
    assert "services:" in rendered


def test_k8s_deployment_renders_envfrom() -> None:
    rendered = _render_k8s_deployment(_ctx(slug="demo"))
    assert "configMapRef:" in rendered
    assert "name: demo-env" in rendered


def test_k8s_service_targets_port() -> None:
    rendered = _render_k8s_service(_ctx(port=9000))
    parsed = yaml.safe_load(rendered)
    assert parsed["spec"]["ports"][0]["targetPort"] == 9000


def test_template_constants_have_no_unrendered_placeholders() -> None:
    # Sanity: smoke-render the inline source. If we ever break a Jinja name,
    # this catches it without needing the CLI path.
    rendered = _render_compose(_ctx())
    assert "{{" not in rendered
    assert "{{" not in _COMPOSE_TEMPLATE.replace("{{ slug }}", "").replace("{{ image }}", "").replace("{{ port }}", "")
