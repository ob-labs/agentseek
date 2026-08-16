from __future__ import annotations

from typing import cast

import pytest

import agentseek.cli.lifecycle.environment as environment_module
from agentseek.cli.lifecycle.dotenv_adapter import parse_lifecycle_dotenv
from agentseek.cli.lifecycle.environment import (
    EnvironmentOrigin,
    LifecycleDotenvError,
    LifecycleEnvironmentSnapshot,
    resolve_lifecycle_environment,
)


@pytest.mark.parametrize(
    ("contents", "category", "canary"),
    [
        ("NUL_KEY_CANARY\x00TAIL=value\n", "variable name", "NUL_KEY_CANARY"),
        ("'EQUALS_KEY_CANARY=TAIL'=value\n", "variable name", "EQUALS_KEY_CANARY"),
        ("SAFE=${AMBIENT}\n", "resolved value", "NUL_VALUE_CANARY"),
    ],
    ids=["nul-key", "equals-key", "resolved-value"],
)
def test_dotenv_adapter_rejects_subprocess_incompatible_bindings_without_echoing_content(
    tmp_path,
    contents,
    category,
    canary,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(contents, encoding="utf-8")

    with pytest.raises(LifecycleDotenvError) as raised:
        parse_lifecycle_dotenv(
            env_file,
            ambient={"AMBIENT": f"prefix\x00{canary}"},
        )

    diagnostic = str(raised.value)
    assert raised.value.line == 1
    assert category in diagnostic
    assert canary not in diagnostic
    assert "\x00" not in diagnostic
    assert "\\x00" not in diagnostic


def test_dotenv_adapter_preserves_physical_order_empty_and_unicode_values(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BASE=模型\nDEPENDENT=${BASE}/路径\nEQUALS_VALUE=left=right\nEXPLICIT_EMPTY=\nVALUELESS\n",
        encoding="utf-8",
    )

    values = parse_lifecycle_dotenv(env_file, ambient={"BASE": "ambient"})

    assert values == {
        "BASE": "模型",
        "DEPENDENT": "模型/路径",
        "EQUALS_VALUE": "left=right",
        "EXPLICIT_EMPTY": "",
        "VALUELESS": None,
    }


def test_snapshot_applies_only_nonempty_launch_values_over_dotenv(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OVERRIDE=from-dotenv\nEMPTY_FALLBACK=from-dotenv\nDOTENV_ONLY=dotenv\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("OVERRIDE", "from-shell")
    monkeypatch.setenv("EMPTY_FALLBACK", "")
    monkeypatch.setenv("EMPTY_LAUNCH_ONLY", "")

    snapshot = resolve_lifecycle_environment(env_file=env_file)

    assert snapshot.values["OVERRIDE"] == "from-shell"
    assert snapshot.origins["OVERRIDE"] is EnvironmentOrigin.LAUNCH_ENVIRONMENT
    assert snapshot.values["EMPTY_FALLBACK"] == "from-dotenv"
    assert snapshot.origins["EMPTY_FALLBACK"] is EnvironmentOrigin.ENV_FILE
    assert snapshot.values["DOTENV_ONLY"] == "dotenv"
    assert "EMPTY_LAUNCH_ONLY" not in snapshot.values


def test_snapshot_preserves_dotenv_empty_and_omits_valueless_binding(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("EXPLICIT_EMPTY=\nUNICODE=模型/路径\nVALUELESS\n", encoding="utf-8")
    monkeypatch.delenv("EXPLICIT_EMPTY", raising=False)
    monkeypatch.delenv("UNICODE", raising=False)
    monkeypatch.delenv("VALUELESS", raising=False)

    snapshot = resolve_lifecycle_environment(env_file=env_file)

    assert "EXPLICIT_EMPTY" in snapshot.values
    assert snapshot.values["EXPLICIT_EMPTY"] == ""
    assert snapshot.origins["EXPLICIT_EMPTY"] is EnvironmentOrigin.ENV_FILE
    assert snapshot.values["UNICODE"] == "模型/路径"
    assert snapshot.origins["UNICODE"] is EnvironmentOrigin.ENV_FILE
    assert "VALUELESS" not in snapshot.values
    assert "VALUELESS" not in snapshot.origins


def test_snapshot_uses_file_local_physical_order_and_parses_once(tmp_path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("BASE=file\nDEPENDENT=${BASE}/v1\n", encoding="utf-8")
    monkeypatch.setenv("BASE", "shell")
    calls: list[object] = []
    real_parse = environment_module.parse_lifecycle_dotenv

    def counting_parse(path, *, ambient):
        calls.append(path)
        return real_parse(path, ambient=ambient)

    monkeypatch.setattr(environment_module, "parse_lifecycle_dotenv", counting_parse)

    snapshot = resolve_lifecycle_environment(env_file=env_file)

    assert calls == [env_file]
    assert snapshot.values["BASE"] == "shell"
    assert snapshot.values["DEPENDENT"] == "file/v1"
    assert snapshot.origins["DEPENDENT"] is EnvironmentOrigin.ENV_FILE


def test_snapshot_is_immutable_and_returns_defensive_process_copies() -> None:
    source_values = {"KEY": "original"}
    source_origins = {"KEY": EnvironmentOrigin.ENV_FILE}
    snapshot = LifecycleEnvironmentSnapshot(
        values=source_values,
        origins=source_origins,
    )
    source_values["KEY"] = "source-mutated"
    source_origins["KEY"] = EnvironmentOrigin.LAUNCH_ENVIRONMENT

    with pytest.raises(TypeError):
        cast("dict[str, str]", snapshot.values)["KEY"] = "mutated"
    with pytest.raises(TypeError):
        cast("dict[str, EnvironmentOrigin]", snapshot.origins)["KEY"] = EnvironmentOrigin.LAUNCH_ENVIRONMENT

    child_environment = snapshot.as_subprocess_env()
    child_environment["KEY"] = "child-only"

    assert snapshot.values["KEY"] == "original"
    assert snapshot.origins["KEY"] is EnvironmentOrigin.ENV_FILE
    assert snapshot.as_subprocess_env()["KEY"] == "original"


def test_snapshot_repr_never_contains_resolved_values() -> None:
    snapshot = LifecycleEnvironmentSnapshot(
        values={"API_KEY": "secret-sentinel-7f3a"},
        origins={"API_KEY": EnvironmentOrigin.LAUNCH_ENVIRONMENT},
    )

    rendered = repr(snapshot)

    assert "secret-sentinel-7f3a" not in rendered
    assert "API_KEY" in rendered
    assert "launch_environment" in rendered


def test_snapshot_rejects_mismatched_value_and_origin_keys() -> None:
    with pytest.raises(ValueError, match="same keys"):
        LifecycleEnvironmentSnapshot(
            values={"VALUE_ONLY": "secret-sentinel"},
            origins={"ORIGIN_ONLY": EnvironmentOrigin.ENV_FILE},
        )


def test_resolver_uses_captured_launch_mapping_when_live_environment_changes(
    tmp_path,
    monkeypatch,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("DEPENDENT=${BASE}/v1\n", encoding="utf-8")
    monkeypatch.setenv("BASE", "captured")
    real_parse = environment_module.parse_lifecycle_dotenv

    def mutate_after_capture(path, *, ambient):
        monkeypatch.setenv("BASE", "changed-after-capture")
        return real_parse(path, ambient=ambient)

    monkeypatch.setattr(environment_module, "parse_lifecycle_dotenv", mutate_after_capture)

    snapshot = resolve_lifecycle_environment(env_file=env_file)

    assert snapshot.values["BASE"] == "captured"
    assert snapshot.values["DEPENDENT"] == "captured/v1"


@pytest.mark.parametrize("contents", ['BROKEN "value"\n', 'UNTERMINATED="value\n'])
def test_resolver_rejects_malformed_dotenv_without_partial_snapshot(
    tmp_path,
    contents,
) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=must-not-leak\n" + contents + "AFTER=value\n", encoding="utf-8")

    with pytest.raises(LifecycleDotenvError) as raised:
        resolve_lifecycle_environment(env_file=env_file, launch_environment={})

    assert raised.value.line == 2
    assert "must-not-leak" not in str(raised.value)


@pytest.mark.parametrize(
    "contents",
    [
        "NUL_KEY_CANARY\x00TAIL=value\n",
        "'EQUALS_KEY_CANARY=TAIL'=value\n",
        "SAFE=value\x00NUL_VALUE_CANARY\n",
    ],
    ids=["nul-key", "equals-key", "resolved-value"],
)
def test_snapshot_rejects_subprocess_incompatible_dotenv_binding_without_partial_result(tmp_path, contents) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(contents, encoding="utf-8")

    with pytest.raises(LifecycleDotenvError):
        resolve_lifecycle_environment(env_file=env_file, launch_environment={})


def test_resolver_rejects_missing_and_invalid_utf8_sources(tmp_path) -> None:
    with pytest.raises(LifecycleDotenvError, match="does not exist"):
        resolve_lifecycle_environment(
            env_file=tmp_path / "missing.env",
            launch_environment={},
        )
    invalid = tmp_path / "invalid.env"
    invalid.write_bytes(b"TOKEN=\xff\n")
    with pytest.raises(LifecycleDotenvError, match="not valid UTF-8"):
        resolve_lifecycle_environment(env_file=invalid, launch_environment={})
