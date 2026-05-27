from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from agentseek_contextseek.plugin import (
    ContextSeekPlugin,
    _extract_text,
    _format_context_block,
    _inject_context,
)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def test_extract_text_from_messages():
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hello"},
    ]
    assert _extract_text(messages) == "hello"


def test_extract_text_returns_empty_when_no_user():
    assert _extract_text([{"role": "assistant", "content": "hi"}]) == ""


def test_inject_context_into_string_prompt():
    result = _inject_context("user query", "[ContextSeek]\n- fact")
    assert isinstance(result, str)
    assert result.startswith("[ContextSeek]")
    assert "user query" in result


def test_inject_context_into_messages_with_system():
    messages = [{"role": "system", "content": "base"}, {"role": "user", "content": "q"}]
    result = _inject_context(messages, "[ctx]")
    assert isinstance(result, list)
    assert "[ctx]" in result[0]["content"]


def test_inject_context_prepends_system_when_absent():
    messages = [{"role": "user", "content": "q"}]
    result = _inject_context(messages, "[ctx]")
    assert isinstance(result, list)
    assert result[0]["role"] == "system"
    assert result[0]["content"] == "[ctx]"


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
    state = {"chat_id": "chat42", "session_id": "ses99"}
    scope = plugin._scope_from_state(state)
    assert scope == "default/chat42/ses99"


# ---------------------------------------------------------------------------
# before_model hook
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_before_model_injects_context():
    plugin = ContextSeekPlugin()
    hit = MagicMock()
    hit.item.stage.value = "knowledge"
    hit.item.summary = "a relevant fact"

    mock_client = MagicMock()
    mock_client.retrieve.return_value = [hit]
    plugin._client = mock_client
    plugin._client_initialized = True

    result = await plugin.before_model(
        prompt="what is OceanBase?",
        session_id="s1",
        state={"chat_id": "c1"},
    )
    assert result is not None
    assert "a relevant fact" in result


@pytest.mark.anyio
async def test_before_model_returns_none_on_no_hits():
    plugin = ContextSeekPlugin()
    mock_client = MagicMock()
    mock_client.retrieve.return_value = []
    plugin._client = mock_client
    plugin._client_initialized = True

    result = await plugin.before_model(prompt="hi", session_id="s1", state={})
    assert result is None


@pytest.mark.anyio
async def test_before_model_returns_none_when_client_unavailable():
    plugin = ContextSeekPlugin()
    plugin._client = None
    plugin._client_initialized = True

    result = await plugin.before_model(prompt="hi", session_id="s1", state={})
    assert result is None


# ---------------------------------------------------------------------------
# after_model hook
# ---------------------------------------------------------------------------


@pytest.mark.anyio
async def test_after_model_calls_add():
    plugin = ContextSeekPlugin()
    mock_client = MagicMock()
    plugin._client = mock_client
    plugin._client_initialized = True

    await plugin.after_model(prompt="q", response="answer text", session_id="s1", state={"chat_id": "c1"})
    mock_client.add.assert_called_once()
    call_kwargs = mock_client.add.call_args
    assert "agent-response" in call_kwargs.kwargs.get("tags", [])


@pytest.mark.anyio
async def test_after_model_skips_empty_response():
    plugin = ContextSeekPlugin()
    mock_client = MagicMock()
    plugin._client = mock_client
    plugin._client_initialized = True

    await plugin.after_model(prompt="q", response="", session_id="s1", state={})
    mock_client.add.assert_not_called()
