"""Tests for optimized template fetching with tarball API and embedded index."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest
import tarfile

from agentseek.cli.commands.create import (
    PARTIAL_CACHE_DIR,
    _download_template_tarball,
    _load_template_descriptions,
    _prepare_templates_root,
    _prepare_templates_root_optimized,
    _show_templates,
    _templates_from_descriptions,
)


def _make_tarball(paths: list[str]) -> bytes:
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path in paths:
            data = b"content"
            info = tarfile.TarInfo(name=path)
            info.size = len(data)
            tar.addfile(info, fileobj=BytesIO(data))
    return buffer.getvalue()


def _make_complete_templates_root(repo_root: Path) -> Path:
    templates_root = repo_root / "templates"
    template_dir = templates_root / "langchain" / "default"
    project_root = template_dir / "{{cookiecutter.project_slug}}"
    project_root.mkdir(parents=True)
    (templates_root / "index.json").write_text(
        json.dumps({"langchain/default": "Default LangChain template."}),
        encoding="utf-8",
    )
    (template_dir / "cookiecutter.json").write_text(
        json.dumps({"project_slug": "demo"}),
        encoding="utf-8",
    )
    (project_root / "README.md").write_text("# Demo\n", encoding="utf-8")
    return templates_root


def test_load_template_descriptions_uses_embedded_fallback() -> None:
    """Embedded catalogue is used when no on-disk templates root is available."""
    with patch("agentseek.cli.commands.create._local_templates_root", return_value=None):
        descriptions = _load_template_descriptions(templates_root=None)

    assert isinstance(descriptions, dict)
    assert len(descriptions) > 0
    assert "bub/default" in descriptions
    assert "langchain/default" in descriptions
    assert "deepagents/sandbox" in descriptions


def test_embedded_catalogue_matches_canonical_index() -> None:
    """Embedded catalogue must stay in sync with templates/index.json."""
    root = Path(__file__).resolve().parents[2]
    canonical = json.loads((root / "templates" / "index.json").read_text(encoding="utf-8"))
    embedded = json.loads(
        (root / "src" / "agentseek" / "data" / "templates_index.json").read_text(encoding="utf-8")
    )
    assert embedded == canonical


def test_load_template_descriptions_prefers_local(tmp_path: Path) -> None:
    """On-disk index.json wins over the embedded catalogue."""
    templates_root = tmp_path / "templates"
    templates_root.mkdir()
    custom_index = {
        "custom/template": "A custom template for testing",
        "another/one": "Another test template",
    }
    (templates_root / "index.json").write_text(json.dumps(custom_index), encoding="utf-8")

    descriptions = _load_template_descriptions(templates_root=templates_root)

    assert descriptions == custom_index
    assert "custom/template" in descriptions
    assert "bub/default" not in descriptions


def test_load_template_descriptions_handles_invalid_json(tmp_path: Path) -> None:
    """Invalid local index falls back to the embedded catalogue."""
    templates_root = tmp_path / "templates"
    templates_root.mkdir()
    (templates_root / "index.json").write_text("not valid json", encoding="utf-8")

    descriptions = _load_template_descriptions(templates_root=templates_root)

    assert isinstance(descriptions, dict)
    assert "bub/default" in descriptions


def test_templates_from_descriptions_sorted_and_typed() -> None:
    descriptions = {
        "bub/default": "x",
        "langchain/default": "y",
        "langchain/agentic-rag": "z",
        "deepagents/sandbox": "s",
    }
    assert _templates_from_descriptions("langchain", descriptions) == ["agentic-rag", "default"]
    assert _templates_from_descriptions("bub", descriptions) == ["default"]


@pytest.mark.parametrize(
    ("project_type", "template_name"),
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
    expected_url = "https://github.com/ob-labs/agentseek/archive/refs/heads/main.tar.gz"
    payload = _make_tarball(
        [
            f"agentseek-main/templates/{project_type}/{template_name}/cookiecutter.json",
        ]
    )

    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[payload])
        mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_stream.return_value.__exit__ = Mock(return_value=None)

        result = _download_template_tarball(project_type, template_name)

        mock_stream.assert_called_once()
        assert mock_stream.call_args[0][1] == expected_url
        assert result is not None
        assert (result / project_type / template_name / "cookiecutter.json").is_file()


def test_download_template_tarball_returns_none_on_http_error(tmp_path: Path) -> None:
    """Network failures must return None so callers can full-clone."""
    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_stream.side_effect = httpx.ConnectError("network down")

        result = _download_template_tarball("langchain", "default")

        assert result is None
        # Must not create the full-repo cookiecutter cache on failure.
        assert not (tmp_path / "agentseek").exists()


def test_download_template_tarball_uses_partial_cache(tmp_path: Path) -> None:
    """A complete single-template cache hit skips the network."""
    cache_dir = tmp_path / PARTIAL_CACHE_DIR / "templates" / "langchain" / "default"
    cache_dir.mkdir(parents=True)
    (cache_dir / "cookiecutter.json").write_text("{}", encoding="utf-8")

    with (
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
    ):
        result = _download_template_tarball("langchain", "default")

        assert result == tmp_path / PARTIAL_CACHE_DIR / "templates"
        mock_stream.assert_not_called()


def test_download_template_tarball_extracts_only_target_template(tmp_path: Path) -> None:
    payload = _make_tarball(
        [
            "agentseek-main/templates/langchain/default/cookiecutter.json",
            "agentseek-main/templates/langchain/default/README.md",
            "agentseek-main/templates/langchain/agentic-rag/cookiecutter.json",
            "agentseek-main/templates/bub/default/cookiecutter.json",
        ]
    )

    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[payload])
        mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_stream.return_value.__exit__ = Mock(return_value=None)

        result = _download_template_tarball("langchain", "default")

        assert result is not None
        extracted = result / "langchain" / "default"
        assert extracted.exists()
        assert (extracted / "cookiecutter.json").exists()
        assert not (result / "bub" / "default").exists()
        assert not (result / "langchain" / "agentic-rag").exists()
        # Partial cache must not touch the full-repo cache path.
        assert not (tmp_path / "agentseek").exists()


def test_download_template_tarball_returns_none_if_template_missing(tmp_path: Path) -> None:
    payload = _make_tarball(["agentseek-main/README.md"])

    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[payload])
        mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_stream.return_value.__exit__ = Mock(return_value=None)

        assert _download_template_tarball("nonexistent", "template") is None
        assert not (tmp_path / "agentseek").exists()


def test_download_template_tarball_rejects_path_traversal(tmp_path: Path) -> None:
    payload = _make_tarball(
        [
            "agentseek-main/templates/langchain/default/../../evil.txt",
            "agentseek-main/templates/langchain/default/cookiecutter.json",
        ]
    )

    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[payload])
        mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_stream.return_value.__exit__ = Mock(return_value=None)

        # Traversal members are rejected; extraction fails closed with None.
        assert _download_template_tarball("langchain", "default") is None


def test_download_template_tarball_replaces_incomplete_cache(tmp_path: Path) -> None:
    """Incomplete previous attempts must be replaced, not crash on move."""
    incomplete = tmp_path / PARTIAL_CACHE_DIR / "templates" / "langchain" / "default"
    incomplete.mkdir(parents=True)
    (incomplete / "README.md").write_text("stale", encoding="utf-8")

    payload = _make_tarball(
        [
            "agentseek-main/templates/langchain/default/cookiecutter.json",
            "agentseek-main/templates/langchain/default/README.md",
        ]
    )

    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[payload])
        mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_stream.return_value.__exit__ = Mock(return_value=None)

        result = _download_template_tarball("langchain", "default")

        assert result is not None
        assert (result / "langchain" / "default" / "cookiecutter.json").is_file()


def test_download_failure_fallback_to_clone(tmp_path: Path) -> None:
    """Regression: download failure must hand off to an actual full clone."""
    full_repo = tmp_path / "downloaded-agentseek"
    templates_root = _make_complete_templates_root(full_repo)
    clone_calls: list[tuple[str, str | None, str, bool]] = []

    def fake_clone(
        repo_url: str,
        *,
        checkout: str | None = None,
        clone_to_dir: Path | str = ".",
        no_input: bool = False,
    ) -> str:
        clone_calls.append((repo_url, checkout, str(clone_to_dir), no_input))
        return str(full_repo)

    with (
        patch("agentseek.cli.commands.create._download_template_tarball", return_value=None) as mock_download,
        patch("agentseek.cli.commands.create._local_templates_root", return_value=None),
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path / "cookiecutters")}),
        patch("cookiecutter.vcs.clone", side_effect=fake_clone),
    ):
        result = _prepare_templates_root_optimized("langchain", "default")

        mock_download.assert_called_once_with("langchain", "default")
        assert clone_calls == [("https://github.com/ob-labs/agentseek", None, str(tmp_path / "cookiecutters"), True)]
        assert result == templates_root


def test_offline_listing_works_without_network() -> None:
    """Regression: --list-templates must not clone when the embedded index exists."""
    with (
        patch("agentseek.cli.commands.create._local_templates_root", return_value=None),
        patch("agentseek.cli.commands.create._prepare_templates_root") as mock_prepare,
        patch("agentseek.cli.commands.create._print_all_templates") as mock_print,
    ):
        _show_templates(project_type=None, checkout=None, filter_keyword=None)

        mock_prepare.assert_not_called()
        mock_print.assert_called_once()
        # templates_root is None in offline mode
        assert mock_print.call_args[0][0] is None


def test_partial_cache_does_not_block_full_clone(tmp_path: Path) -> None:
    """Regression: partial cache must never be treated as a full-repo cache hit."""
    # Prior partial download left behind a single-template cache.
    partial = tmp_path / PARTIAL_CACHE_DIR / "templates" / "langchain" / "default"
    partial.mkdir(parents=True)
    (partial / "cookiecutter.json").write_text("{}", encoding="utf-8")

    full_repo = tmp_path / "downloaded-agentseek"
    templates_root = _make_complete_templates_root(full_repo)
    clone_calls: list[str] = []

    def fake_clone(
        repo_url: str,
        *,
        checkout: str | None = None,
        clone_to_dir: Path | str = ".",
        no_input: bool = False,
    ) -> str:
        clone_calls.append(repo_url)
        return str(full_repo)

    with (
        patch("agentseek.cli.commands.create._local_templates_root", return_value=None),
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("cookiecutter.vcs.clone", side_effect=fake_clone),
    ):
        result = _prepare_templates_root(checkout=None)

        assert clone_calls == ["https://github.com/ob-labs/agentseek"]
    assert result == templates_root


def test_empty_full_repo_cache_still_clones(tmp_path: Path) -> None:
    """An empty/incomplete ~/.cookiecutters/agentseek must not skip clone()."""
    empty_cache = tmp_path / "agentseek"
    empty_cache.mkdir()
    full_repo = tmp_path / "downloaded-agentseek"
    templates_root = _make_complete_templates_root(full_repo)
    clone_calls: list[str] = []

    def fake_clone(
        repo_url: str,
        *,
        checkout: str | None = None,
        clone_to_dir: Path | str = ".",
        no_input: bool = False,
    ) -> str:
        clone_calls.append(repo_url)
        return str(full_repo)

    with (
        patch("agentseek.cli.commands.create._local_templates_root", return_value=None),
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("cookiecutter.vcs.clone", side_effect=fake_clone),
    ):
        result = _prepare_templates_root(checkout=None)

        assert clone_calls == ["https://github.com/ob-labs/agentseek"]
    assert result == templates_root


def test_create_resolves_template_before_fetch(tmp_path: Path) -> None:
    """Regression: --template / --no-input must feed the tarball path."""
    from typer.testing import CliRunner

    from agentseek.cli.commands import create as create_module
    from agentseek.cli.commands.create import TemplateSource
    from tests.cli_commands.helpers import build_command_app

    partial_root = tmp_path / PARTIAL_CACHE_DIR / "templates"
    template_dir = partial_root / "langchain" / "default"
    template_dir.mkdir(parents=True)
    (template_dir / "cookiecutter.json").write_text(
        json.dumps({"project_slug": "demo"}),
        encoding="utf-8",
    )

    fetch_calls: list[tuple[str | None, str | None]] = []

    def fake_prepare(
        project_type: str | None = None,
        template_name: str | None = None,
        checkout: str | None = None,
    ) -> Path:
        fetch_calls.append((project_type, template_name))
        return partial_root

    def fake_cookiecutter(source, *, output_dir, no_input):  # noqa: ANN001
        return Path(output_dir) / "demo"

    with (
        patch.object(create_module, "_local_templates_root", return_value=None),
        patch.object(create_module, "_prepare_templates_root_optimized", side_effect=fake_prepare),
        patch.object(create_module, "_run_cookiecutter", side_effect=fake_cookiecutter),
        patch.object(create_module, "_resolve_type_template") as mock_resolve,
    ):
        mock_resolve.return_value = TemplateSource(template=str(template_dir))
        result = CliRunner().invoke(
            build_command_app(),
            ["create", "langchain", "--template", "default", "--no-input", "--output-dir", str(tmp_path)],
        )

    assert result.exit_code == 0, result.output
    assert fetch_calls == [("langchain", "default")]
