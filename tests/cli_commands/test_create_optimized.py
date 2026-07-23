"""Tests for optimized template fetching with tarball API and embedded index."""

from __future__ import annotations

import hashlib
import json
import tarfile
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest

from agentseek.cli.commands import create as create_module
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
            data = b'{"project_slug": "demo"}' if path.endswith("cookiecutter.json") else b"content"
            info = tarfile.TarInfo(name=path)
            info.size = len(data)
            tar.addfile(info, fileobj=BytesIO(data))
    return buffer.getvalue()


def _valid_template_tarball() -> bytes:
    return _make_tarball(
        [
            "agentseek-main/templates/langchain/default/cookiecutter.json",
            "agentseek-main/templates/langchain/default/{{cookiecutter.project_slug}}/README.md",
        ]
    )


def _make_tarball_with_unsafe_member(member_type: bytes) -> bytes:
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        unsafe = tarfile.TarInfo(name="agentseek-main/outside-target")
        unsafe.type = member_type
        unsafe.linkname = "../../outside" if member_type == tarfile.LNKTYPE else ""
        tar.addfile(unsafe)
        for path, data in (
            (
                "agentseek-main/templates/langchain/default/cookiecutter.json",
                b'{"project_slug": "demo"}',
            ),
            (
                "agentseek-main/templates/langchain/default/{{cookiecutter.project_slug}}/README.md",
                b"content",
            ),
        ):
            info = tarfile.TarInfo(name=path)
            info.size = len(data)
            tar.addfile(info, fileobj=BytesIO(data))
    return buffer.getvalue()


def _make_complete_templates_root(repo_root: Path) -> Path:
    templates_root = repo_root / "templates"
    templates_root.mkdir(parents=True)
    catalogue = json.loads(
        (Path(__file__).resolve().parents[2] / "src" / "agentseek" / "data" / "templates_index.json").read_text(
            encoding="utf-8"
        )
    )
    (templates_root / "index.json").write_text(json.dumps(catalogue), encoding="utf-8")
    for template in catalogue:
        template_dir = templates_root / template
        project_root = template_dir / "{{cookiecutter.project_slug}}"
        project_root.mkdir(parents=True)
        (template_dir / "cookiecutter.json").write_text(
            json.dumps({"project_slug": "demo"}),
            encoding="utf-8",
        )
        (project_root / "README.md").write_text("# Demo\n", encoding="utf-8")
    return templates_root


def test_embedded_catalogue_digest_uses_exact_packaged_bytes() -> None:
    root = Path(__file__).resolve().parents[2]
    packaged = root / "src" / "agentseek" / "data" / "templates_index.json"

    assert create_module._embedded_catalogue_digest() == hashlib.sha256(packaged.read_bytes()).hexdigest()


def test_cache_metadata_round_trip_is_atomic(tmp_path: Path) -> None:
    metadata_path = tmp_path / "nested" / ".agentseek-cache.json"
    expected = create_module._expected_cache_metadata(
        repository=create_module.REPO_URL,
        ref="main",
        template_key="langchain/default",
    )

    create_module._write_cache_metadata(metadata_path, expected)

    assert create_module._cache_metadata_matches(metadata_path, expected)
    assert not metadata_path.with_name(f"{metadata_path.name}.tmp").exists()


@pytest.mark.parametrize(
    "payload",
    [
        None,
        "not-json",
        {},
        {
            "schema_version": 999,
            "repository": "https://github.com/other/repo",
            "ref": "old",
            "catalog_digest": "0" * 64,
            "template_key": "bub/default",
        },
    ],
    ids=["missing", "malformed", "empty", "mismatched"],
)
def test_cache_metadata_rejects_missing_malformed_or_mismatched(
    tmp_path: Path,
    payload: object | None,
) -> None:
    metadata_path = tmp_path / ".agentseek-cache.json"
    expected = create_module._expected_cache_metadata(
        repository=create_module.REPO_URL,
        ref="main",
        template_key="langchain/default",
    )
    if payload is not None:
        text = payload if isinstance(payload, str) else json.dumps(payload)
        metadata_path.write_text(text, encoding="utf-8")

    assert not create_module._cache_metadata_matches(metadata_path, expected)


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
            (
                f"agentseek-main/templates/{project_type}/{template_name}/"
                "{{cookiecutter.project_slug}}/README.md"
            ),
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
    project_root = cache_dir / "{{cookiecutter.project_slug}}"
    project_root.mkdir(parents=True)
    (cache_dir / "cookiecutter.json").write_text(
        json.dumps({"project_slug": "demo"}),
        encoding="utf-8",
    )
    (project_root / "README.md").write_text("# Demo\n", encoding="utf-8")
    metadata = create_module._expected_cache_metadata(
        repository=create_module.REPO_URL,
        ref="main",
        template_key="langchain/default",
    )
    create_module._write_cache_metadata(
        create_module._partial_cache_metadata_path(tmp_path, "langchain", "default"),
        metadata,
    )

    with (
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
    ):
        result = _download_template_tarball("langchain", "default")

        assert result == tmp_path / PARTIAL_CACHE_DIR / "templates"
        mock_stream.assert_not_called()


def test_download_template_tarball_refetches_partial_cache_without_metadata(tmp_path: Path) -> None:
    """A renderable legacy partial cache without identity metadata is stale."""
    cache_dir = tmp_path / PARTIAL_CACHE_DIR / "templates" / "langchain" / "default"
    project_root = cache_dir / "{{cookiecutter.project_slug}}"
    project_root.mkdir(parents=True)
    (cache_dir / "cookiecutter.json").write_text(
        json.dumps({"project_slug": "demo"}),
        encoding="utf-8",
    )
    (project_root / "README.md").write_text("# Demo\n", encoding="utf-8")

    with (
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_stream.side_effect = httpx.ConnectError("network down")

        result = _download_template_tarball("langchain", "default")

        assert result is None
        mock_stream.assert_called_once()


def test_download_template_tarball_refetches_incomplete_partial_cache(tmp_path: Path) -> None:
    """A malformed single-template cache must not suppress download/fallback."""
    cache_dir = tmp_path / PARTIAL_CACHE_DIR / "templates" / "langchain" / "default"
    cache_dir.mkdir(parents=True)
    (cache_dir / "cookiecutter.json").write_text("{}", encoding="utf-8")

    with (
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_stream.side_effect = httpx.ConnectError("network down")

        result = _download_template_tarball("langchain", "default")

        assert result is None
        mock_stream.assert_called_once()


def test_download_template_tarball_does_not_cache_incomplete_download(tmp_path: Path) -> None:
    """A downloaded subtree must be renderable before it becomes cache state."""
    payload = _make_tarball(
        ["agentseek-main/templates/langchain/default/cookiecutter.json"]
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

        assert result is None
        assert not (
            tmp_path / PARTIAL_CACHE_DIR / "templates" / "langchain" / "default"
        ).exists()


def test_download_template_tarball_extracts_only_target_template(tmp_path: Path) -> None:
    payload = _make_tarball(
        [
            "agentseek-main/templates/langchain/default/cookiecutter.json",
            "agentseek-main/templates/langchain/default/{{cookiecutter.project_slug}}/README.md",
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


@pytest.mark.parametrize("template_name", ["../outside", r"..\outside", "nested/name"])
def test_download_template_tarball_rejects_unsafe_template_key(
    tmp_path: Path,
    template_name: str,
) -> None:
    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        assert _download_template_tarball("langchain", template_name) is None
        mock_stream.assert_not_called()


def test_download_template_tarball_rejects_oversized_content_length(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    payload = _valid_template_tarball()
    monkeypatch.setattr(create_module, "MAX_ARCHIVE_DOWNLOAD_BYTES", len(payload) - 1)

    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_response = Mock()
        mock_response.headers = {"Content-Length": str(len(payload))}
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[payload])
        mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_stream.return_value.__exit__ = Mock(return_value=None)

        result = _download_template_tarball("langchain", "default")

        assert result is None
        mock_response.iter_bytes.assert_not_called()


def test_download_template_tarball_rejects_oversized_stream(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    payload = _valid_template_tarball()
    monkeypatch.setattr(create_module, "MAX_ARCHIVE_DOWNLOAD_BYTES", len(payload) - 1)

    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[payload[:10], payload[10:]])
        mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_stream.return_value.__exit__ = Mock(return_value=None)

        assert _download_template_tarball("langchain", "default") is None


@pytest.mark.parametrize(
    ("limit_name", "limit"),
    [
        ("MAX_ARCHIVE_MEMBERS", 1),
        ("MAX_ARCHIVE_MEMBER_BYTES", 6),
        ("MAX_ARCHIVE_UNCOMPRESSED_BYTES", 20),
    ],
)
def test_download_template_tarball_enforces_archive_limits(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    limit_name: str,
    limit: int,
) -> None:
    monkeypatch.setattr(create_module, limit_name, limit)
    payload = _valid_template_tarball()

    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[payload])
        mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_stream.return_value.__exit__ = Mock(return_value=None)

        assert _download_template_tarball("langchain", "default") is None


@pytest.mark.parametrize("member_type", [tarfile.LNKTYPE, tarfile.CHRTYPE], ids=["hardlink", "device"])
def test_download_template_tarball_rejects_unsafe_members_outside_target(
    tmp_path: Path,
    member_type: bytes,
) -> None:
    payload = _make_tarball_with_unsafe_member(member_type)

    with (
        patch("agentseek.cli.commands.create.httpx.stream") as mock_stream,
        patch("cookiecutter.config.get_user_config", return_value={"cookiecutters_dir": str(tmp_path)}),
        patch("agentseek.cli.commands.create.typer.echo"),
    ):
        mock_response = Mock()
        mock_response.headers = {}
        mock_response.raise_for_status = Mock()
        mock_response.iter_bytes = Mock(return_value=[payload])
        mock_stream.return_value.__enter__ = Mock(return_value=mock_response)
        mock_stream.return_value.__exit__ = Mock(return_value=None)

        assert _download_template_tarball("langchain", "default") is None


def test_download_template_tarball_replaces_incomplete_cache(tmp_path: Path) -> None:
    """Incomplete previous attempts must be replaced, not crash on move."""
    incomplete = tmp_path / PARTIAL_CACHE_DIR / "templates" / "langchain" / "default"
    incomplete.mkdir(parents=True)
    (incomplete / "README.md").write_text("stale", encoding="utf-8")

    payload = _make_tarball(
        [
            "agentseek-main/templates/langchain/default/cookiecutter.json",
            "agentseek-main/templates/langchain/default/{{cookiecutter.project_slug}}/README.md",
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


def test_full_cache_requires_matching_metadata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A complete legacy cache without identity metadata must be refreshed."""
    cached_repo = tmp_path / "agentseek"
    _make_complete_templates_root(cached_repo)
    fresh_repo = tmp_path / "downloaded-agentseek"
    templates_root = _make_complete_templates_root(fresh_repo)
    clone_calls: list[str] = []

    def fake_clone(
        repo_url: str,
        *,
        checkout: str | None = None,
        clone_to_dir: Path | str = ".",
        no_input: bool = False,
    ) -> str:
        clone_calls.append(repo_url)
        return str(fresh_repo)

    monkeypatch.setattr(create_module, "_local_templates_root", lambda: None)
    monkeypatch.setattr(create_module, "_load_embedded_template_descriptions", lambda: {
        "langchain/default": "Default LangChain template."
    })
    monkeypatch.setattr("cookiecutter.config.get_user_config", lambda: {"cookiecutters_dir": str(tmp_path)})
    monkeypatch.setattr("cookiecutter.vcs.clone", fake_clone)

    result = _prepare_templates_root(checkout=None)

    assert clone_calls == [create_module.REPO_URL]
    assert result == templates_root


def test_full_cache_reuses_matching_metadata(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A complete cache with matching identity metadata skips clone()."""
    cached_repo = tmp_path / "agentseek"
    templates_root = _make_complete_templates_root(cached_repo)
    metadata = create_module._expected_cache_metadata(
        repository=create_module.REPO_URL,
        ref="main",
    )
    create_module._write_cache_metadata(cached_repo / create_module.CACHE_METADATA_FILENAME, metadata)
    clone_calls: list[str] = []

    monkeypatch.setattr(create_module, "_local_templates_root", lambda: None)
    monkeypatch.setattr(create_module, "_load_embedded_template_descriptions", lambda: {
        "langchain/default": "Default LangChain template."
    })
    monkeypatch.setattr("cookiecutter.config.get_user_config", lambda: {"cookiecutters_dir": str(tmp_path)})
    monkeypatch.setattr("cookiecutter.vcs.clone", lambda *args, **kwargs: clone_calls.append("clone"))

    result = _prepare_templates_root(checkout=None)

    assert clone_calls == []
    assert result == templates_root


def test_full_cache_missing_packaged_template_clones(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A cache index cannot hide a public template missing from the checkout."""
    cached_repo = tmp_path / "agentseek"
    _make_complete_templates_root(cached_repo)
    fresh_repo = tmp_path / "downloaded-agentseek"
    templates_root = _make_complete_templates_root(fresh_repo)
    missing_template = templates_root / "langchain" / "missing"
    missing_project = missing_template / "{{cookiecutter.project_slug}}"
    missing_project.mkdir(parents=True)
    (missing_template / "cookiecutter.json").write_text(
        json.dumps({"project_slug": "demo"}),
        encoding="utf-8",
    )
    (missing_project / "README.md").write_text("# Missing\n", encoding="utf-8")
    clone_calls: list[str] = []

    def fake_clone(*args, **kwargs):
        clone_calls.append("clone")
        return str(fresh_repo)

    monkeypatch.setattr(create_module, "_local_templates_root", lambda: None)
    monkeypatch.setattr(create_module, "_load_embedded_template_descriptions", lambda: {
        "langchain/default": "Default LangChain template.",
        "langchain/missing": "Missing template.",
    })
    monkeypatch.setattr("cookiecutter.config.get_user_config", lambda: {"cookiecutters_dir": str(tmp_path)})
    monkeypatch.setattr("cookiecutter.vcs.clone", fake_clone)

    result = _prepare_templates_root(checkout=None)

    assert clone_calls == ["clone"]
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

    def fake_cookiecutter(source, *, output_dir, no_input):
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
