from __future__ import annotations

from agentseek_contextseek.config import _ALIASES, AGENTSEEK_CTX_PREFIX, apply_contextseek_env_aliases


def test_alias_is_applied_as_fallback():
    env: dict[str, str] = {"AGENTSEEK_CTX_STORAGE_BACKEND": "file"}
    apply_contextseek_env_aliases(env)
    assert env["STORAGE_BACKEND"] == "file"


def test_original_var_takes_precedence():
    env: dict[str, str] = {
        "AGENTSEEK_CTX_STORAGE_BACKEND": "file",
        "STORAGE_BACKEND": "oceanbase",
    }
    apply_contextseek_env_aliases(env)
    assert env["STORAGE_BACKEND"] == "oceanbase"


def test_missing_alias_leaves_no_original():
    env: dict[str, str] = {}
    apply_contextseek_env_aliases(env)
    assert "STORAGE_BACKEND" not in env


def test_all_aliases_covered():
    for key in _ALIASES:
        alias = f"{AGENTSEEK_CTX_PREFIX}{key}"
        env: dict[str, str] = {alias: "test-value"}
        apply_contextseek_env_aliases(env)
        assert env[key] == "test-value", f"{key} not mapped from {alias}"


def test_idempotent():
    env: dict[str, str] = {"AGENTSEEK_CTX_STORAGE_BACKEND": "file"}
    apply_contextseek_env_aliases(env)
    apply_contextseek_env_aliases(env)
    assert env["STORAGE_BACKEND"] == "file"
