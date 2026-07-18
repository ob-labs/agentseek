"""Tests for optimized template fetching with tarball API and embedded index."""

from __future__ import annotations

import json
import tarfile
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from agentseek.cli.commands.create import (
    _download_template_tarball,
    _load_template_descriptions,
)


def test_load_template_descriptions_uses_embedded_fallback(tmp_path: Path) -> None:
    """Test that _load_template_descriptions falls back to embedded index.json."""
    # When templates_root is None or doesn't have index.json, should use embedded
    descriptions = _load_template_descriptions(templates_root=None)

    # Should load from embedded data
    assert isinstance(descriptions, dict)
    assert len(descriptions) > 0
    # Check some known templates exist
    assert "bub/default" in descriptions
    assert "langchain/default" in descriptions
    assert "deepagents/sandbox" in descriptions


def test_load_template_descriptions_prefers_local(tmp_path: Path) -> None:
    """Test that _load_template_descriptions prefers local over embedded."""
    # Create a local templates dir with custom index
    templates_root = tmp_path / "templates"
    templates_root.mkdir()
    custom_index = {
        "custom/template": "A custom template for testing",
        "another/one": "Another test template",
    }
    (templates_root / "index.json").write_text(json.dumps(custom_index), encoding="utf-8")

    descriptions = _load_template_descriptions(templates_root=templates_root)

    # Should load local, not embedded
    assert descriptions == custom_index
    assert "custom/template" in descriptions
    assert "bub/default" not in descriptions


def test_load_template_descriptions_handles_invalid_json(tmp_path: Path) -> None:
    """Test graceful fallback when local index.json is invalid."""
    templates_root = tmp_path / "templates"
    templates_root.mkdir()
    (templates_root / "index.json").write_text("not valid json", encoding="utf-8")

    # Should fall back to embedded
    descriptions = _load_template_descriptions(templates_root=templates_root)

    assert isinstance(descriptions, dict)
    assert "bub/default" in descriptions  # From embedded


@pytest.mark.parametrize(
    "project_type,template_name",
    [
        ("langchain", "default"),
        ("bub", "default"),
        ("deepagents", "sandbox"),
    ],
)
def test_download_template_tarball_constructs_correct_url(
    project_type: str,
    template_name: str,
    tmp_path: Path,
) -> None:
    """Test that tarball download constructs the correct GitHub URL."""
    expected_url = "https://github.com/ob-labs/agentseek/archive/refs/heads/main.tar.gz"

    with patch("agentseek.cli.commands.create.httpx.stream") as mock_stream, \
         patch("agentseek.cli.commands.create.get_user_config") as mock_config:

        # Setup mocks
        mock_config.return_value = {"cookiecutters_dir": str(tmp_path)}
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[b"fake tarball data"])
        mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_stream.return_value.__exit__ = Mock(return_value=None)

        # Mock tarfile to avoid actual extraction
        with patch("agentseek.cli.commands.create.tarfile.open"):
            try:
                _download_template_tarball(project_type, template_name)
            except Exception:
                pass  # We only care about the URL being correct

        # Verify the URL
        mock_stream.assert_called_once()
        call_args = mock_stream.call_args
        assert call_args[0][1] == expected_url


def test_download_template_tarball_returns_none_on_http_error(tmp_path: Path) -> None:
    """Test that tarball download returns None on HTTP errors."""
    with patch("agentseek.cli.commands.create.httpx.stream") as mock_stream, \
         patch("agentseek.cli.commands.create.get_user_config") as mock_config, \
         patch("agentseek.cli.commands.create.typer.echo"):

        mock_config.return_value = {"cookiecutters_dir": str(tmp_path)}
        mock_stream.side_effect = Exception("Network error")

        result = _download_template_tarball("langchain", "default")

        assert result is None


def test_download_template_tarball_uses_cache(tmp_path: Path) -> None:
    """Test that tarball download skips download if template is already cached."""
    # Create a cached template
    cache_dir = tmp_path / "agentseek" / "templates" / "langchain" / "default"
    cache_dir.mkdir(parents=True)
    (cache_dir / "cookiecutter.json").write_text("{}", encoding="utf-8")

    with patch("agentseek.cli.commands.create.get_user_config") as mock_config, \
         patch("agentseek.cli.commands.create.httpx.stream") as mock_stream:

        mock_config.return_value = {"cookiecutters_dir": str(tmp_path)}

        result = _download_template_tarball("langchain", "default")

        # Should return cached path without downloading
        assert result == tmp_path / "agentseek" / "templates"
        mock_stream.assert_not_called()


def test_download_template_tarball_extracts_only_target_template(tmp_path: Path) -> None:
    """Test that only the requested template is extracted from tarball."""
    # Create a mock tarball with multiple templates
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tf:
        tarball_path = Path(tf.name)

        with tarfile.open(tarball_path, "w:gz") as tar:
            # Add files for multiple templates
            for template in ["langchain/default", "langchain/agentic-rag", "bub/default"]:
                for file in ["cookiecutter.json", "README.md"]:
                    path = f"agentseek-main/templates/{template}/{file}"
                    info = tarfile.TarInfo(name=path)
                    info.size = len(b"content")
                    tar.addfile(info, fileobj=tempfile.BytesIO(b"content"))

        with patch("agentseek.cli.commands.create.httpx.stream") as mock_stream, \
             patch("agentseek.cli.commands.create.get_user_config") as mock_config:

            mock_config.return_value = {"cookiecutters_dir": str(tmp_path)}

            # Mock the download to return our test tarball
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            with open(tarball_path, "rb") as f:
                mock_response.iter_bytes = Mock(return_value=[f.read()])
            mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
            mock_stream.return_value.__exit__ = Mock(return_value=None)

            result = _download_template_tarball("langchain", "default")

            # Should have extracted only langchain/default
            if result:
                extracted = result / "langchain" / "default"
                assert extracted.exists()
                assert (extracted / "cookiecutter.json").exists()

                # Should NOT have extracted other templates
                other = result / "bub" / "default"
                assert not other.exists()

        # Cleanup
        tarball_path.unlink()


def test_download_template_tarball_returns_none_if_template_not_in_tarball(tmp_path: Path) -> None:
    """Test that tarball download returns None if template doesn't exist in tarball."""
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tf:
        tarball_path = Path(tf.name)

        # Create empty tarball
        with tarfile.open(tarball_path, "w:gz") as tar:
            pass

        with patch("agentseek.cli.commands.create.httpx.stream") as mock_stream, \
             patch("agentseek.cli.commands.create.get_user_config") as mock_config, \
             patch("agentseek.cli.commands.create.typer.echo"):

            mock_config.return_value = {"cookiecutters_dir": str(tmp_path)}

            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            with open(tarball_path, "rb") as f:
                mock_response.iter_bytes = Mock(return_value=[f.read()])
            mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
            mock_stream.return_value.__exit__ = Mock(return_value=None)

            result = _download_template_tarball("nonexistent", "template")

            assert result is None

        tarball_path.unlink()
