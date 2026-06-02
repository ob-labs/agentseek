from __future__ import annotations

import pytest
from agentseek_contextseek.config import (
    AGENTSEEK_CTX_PREFIX,
    _upstream_env_vars,
    apply_contextseek_env_aliases,
)


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


def test_idempotent():
    env: dict[str, str] = {"AGENTSEEK_CTX_STORAGE_BACKEND": "file"}
    apply_contextseek_env_aliases(env)
    apply_contextseek_env_aliases(env)
    assert env["STORAGE_BACKEND"] == "file"


# ---------------------------------------------------------------------------
# Reflection: the alias surface must track upstream contextseek 1:1.
# ---------------------------------------------------------------------------


def test_reflection_picks_up_known_groups():
    """Spot-check that each documented contextseek group contributes vars."""
    env_vars = _upstream_env_vars()
    # At least one variable per public group exists.
    for prefix in ("STORAGE_", "OB_", "EMBEDDING_", "LLM_", "RETRIEVAL_", "EVOLUTION_"):
        assert any(v.startswith(prefix) for v in env_vars), f"no {prefix}* in {env_vars!r}"


@pytest.mark.parametrize(
    "env_var",
    # Hand-picked invariants we expect contextseek to keep stable.
    ["STORAGE_BACKEND", "OB_HOST", "EMBEDDING_MODEL", "LLM_MODEL", "RETRIEVAL_DEFAULT_K"],
)
def test_known_var_is_aliased(env_var: str):
    env: dict[str, str] = {f"{AGENTSEEK_CTX_PREFIX}{env_var}": "v"}
    apply_contextseek_env_aliases(env)
    assert env[env_var] == "v"


def test_every_reflected_var_is_aliased():
    """Whatever contextseek exposes today should be alias-routable today."""
    for env_var in _upstream_env_vars():
        env: dict[str, str] = {f"{AGENTSEEK_CTX_PREFIX}{env_var}": "test-value"}
        apply_contextseek_env_aliases(env)
        assert env[env_var] == "test-value", f"{env_var} not mapped"
