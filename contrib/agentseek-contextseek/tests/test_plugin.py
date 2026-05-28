from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from agentseek_contextseek.plugin import (
    ContextSeekPlugin,
    _format_context_block,
    _inject_context,
)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def test_inject_context_into_prompt():
    result = _inject_context("user query", "[ContextSeek]\n- fact")
    assert result.startswith("[ContextSeek]")
    assert "user query" in result


def test_format_context_block():
    hit = MagicMock()
    hit.item.stage.value = "knowledge"
    hit.item.summary = "distributed DB fact"
    block = _format_context_block([hit])
    assert "[ContextSeek]" in block
    assert "distributed DB fact" in block


# ---------------------------------------------------------------------------
# Plugin lifecycle
# ---------------------------------------------------------------------------


def test_plugin_init_applies_env_aliases():
    with patch("agentseek_contextseek.plugin.apply_contextseek_env_aliases") as mock_apply:
        ContextSeekPlugin()
    mock_apply.assert_called_once()


def test_get_client_lazy_and_cached():
    plugin = ContextSeekPlugin()
    mock_client = MagicMock()
    with patch("importlib.import_module") as mock_import:
        mock_mod = MagicMock()
        mock_mod.ContextSeek.from_settings.return_value = mock_client
        mock_import.return_value = mock_mod
        c1 = plugin._get_client()
        c2 = plugin._get_client()
    assert c1 is c2
    mock_mod.ContextSeek.from_settings.assert_called_once()


def test_get_client_returns_none_on_failure():
    plugin = ContextSeekPlugin()
    with patch("importlib.import_module", side_effect=Exception("no contextseek")):
        client = plugin._get_client()
    assert client is None


def test_scope_from_state():
    plugin = ContextSeekPlugin()
    message = {"chat_id": "chat42"}
    scope = plugin._scope_from_message(message, "ses99")
    assert scope == "default/chat42/ses99"


# ---------------------------------------------------------------------------
# load_state + build_prompt hooks
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_load_state_returns_context_block_on_hits():
    plugin = ContextSeekPlugin()
    hit = MagicMock()
    hit.item.stage.value = "knowledge"
    hit.item.summary = "a relevant fact"

    mock_client = MagicMock()
    mock_client.retrieve.return_value = [hit]
    plugin._client = mock_client
    plugin._client_initialized = True

    state = await plugin.load_state(
        message={"content": "what is OceanBase?", "chat_id": "c1"},
        session_id="s1",
    )
    assert "_contextseek_block" in state
    assert "a relevant fact" in state["_contextseek_block"]
    assert state["_contextseek_scope"] == "default/c1/s1"


@pytest.mark.anyio
async def test_load_state_returns_scope_only_on_no_hits():
    plugin = ContextSeekPlugin()
    mock_client = MagicMock()
    mock_client.retrieve.return_value = []
    plugin._client = mock_client
    plugin._client_initialized = True

    state = await plugin.load_state(message={"content": "hi"}, session_id="s1")
    assert "_contextseek_block" not in state
    assert state["_contextseek_scope"] == "default/local/s1"


@pytest.mark.anyio
async def test_load_state_returns_empty_when_client_unavailable():
    plugin = ContextSeekPlugin()
    plugin._client = None
    plugin._client_initialized = True

    state = await plugin.load_state(message={"content": "hi"}, session_id="s1")
    assert state == {}


# ---------------------------------------------------------------------------
# build_prompt + save_state hooks
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_build_prompt_injects_context():
    plugin = ContextSeekPlugin()
    result = await plugin.build_prompt(
        message={"content": "what is OceanBase?"},
        session_id="s1",
        state={"_contextseek_block": "[ContextSeek]\n- fact"},
    )
    assert result is not None
    assert result.startswith("[ContextSeek]")
    assert "what is OceanBase?" in result


@pytest.mark.anyio
async def test_build_prompt_returns_none_without_context():
    plugin = ContextSeekPlugin()
    result = await plugin.build_prompt(
        message={"content": "hi"},
        session_id="s1",
        state={},
    )
    assert result is None


@pytest.mark.anyio
async def test_save_state_calls_add():
    plugin = ContextSeekPlugin()
    mock_client = MagicMock()
    plugin._client = mock_client
    plugin._client_initialized = True

    await plugin.save_state(
        session_id="s1",
        state={"_contextseek_scope": "default/c1/s1"},
        message={"chat_id": "c1"},
        model_output="answer text",
    )
    mock_client.add.assert_called_once()
    call_kwargs = mock_client.add.call_args
    assert "agent-response" in call_kwargs.kwargs.get("tags", [])


@pytest.mark.anyio
async def test_save_state_skips_empty_response():
    plugin = ContextSeekPlugin()
    mock_client = MagicMock()
    plugin._client = mock_client
    plugin._client_initialized = True

    await plugin.save_state(
        session_id="s1",
        state={},
        message={"chat_id": "c1"},
        model_output="",
    )
    mock_client.add.assert_not_called()
