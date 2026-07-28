"""Tests for the immutable default template catalog."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import subprocess
import tarfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from importlib.resources import files
from pathlib import Path
from threading import Event

import httpx
import pytest
from typer.testing import CliRunner

from agentseek.cli.catalog import CatalogLock
from agentseek.cli.commands import create as create_module
from agentseek.cli.commands.create import TemplateSource
from tests.cli_commands.helpers import build_command_app

pytestmark = pytest.mark.usefixtures("create_symlink")


_FIXTURE_TEMPLATE_DIGEST = "3f682e624588556b23b29692d8b4f781e78166f56a5905e9def330b36fbd57a9"


def _fixture_lock(lock: CatalogLock) -> CatalogLock:
    """Trust the compact synthetic template tree used by archive unit tests."""
    return replace(
        lock,
        template_digests=dict.fromkeys(lock.templates, _FIXTURE_TEMPLATE_DIGEST),
    )


def _add_tar_file(archive: tarfile.TarFile, name: str, content: bytes, *, mode: int = 0o644) -> None:
    member = tarfile.TarInfo(name)
    member.size = len(content)
    member.mode = mode
    archive.addfile(member, io.BytesIO(content))


def _catalog_archive(
    lock: CatalogLock,
    *,
    key: str = "bub/default",
    index: dict[str, str] | None = None,
    extras: list[tuple[tarfile.TarInfo, bytes | None]] | None = None,
    readme_mode: int = 0o644,
) -> bytes:
    root = "agentseek-templates-fixture"
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        registry = dict(lock.templates) if index is None else index
        _add_tar_file(
            archive,
            f"{root}/{lock.index_path}",
            json.dumps(registry).encode(),
        )
        template_root = f"{root}/{lock.templates_root}/{key}"
        _add_tar_file(
            archive,
            f"{template_root}/cookiecutter.json",
            json.dumps({"project_slug": "demo"}).encode(),
        )
        _add_tar_file(
            archive,
            f"{template_root}/{{{{cookiecutter.project_slug}}}}/README.md",
            b"# Demo\n",
            mode=readme_mode,
        )
        if key != "langchain/default":
            _add_tar_file(
                archive,
                f"{root}/{lock.templates_root}/langchain/default/cookiecutter.json",
                b'{"project_slug":"other"}',
            )
        for member, content in extras or []:
            archive.addfile(member, io.BytesIO(content) if content is not None else None)
    return stream.getvalue()


def test_packaged_catalog_lock_records_the_published_release_pair() -> None:
    """A built client must carry the immutable catalog and core coordinates."""
    lock_bytes = files("agentseek").joinpath("data/catalog-lock.json").read_bytes()
    lock = json.loads(lock_bytes)

    assert lock == {
        "schema_version": 1,
        "catalog_repository": "https://github.com/agentseek-ai/agentseek-templates.git",
        "catalog_commit": "494863bc1b9aab19f9885d716c03ce654fb26014",
        "catalog_release": "v0.1.0",
        "templates_root": "templates",
        "index_path": "templates/index.json",
        "lifecycle_version": 2,
        "core_repository": "https://github.com/ob-labs/agentseek.git",
        "core_commit": "883addad1e2993c4be6fc8ba053f87f25fb5057a",
        "core_release": "core-snapshot-v0.1.0",
        "templates": {
            "bub/default": "Lightweight Bub agent with AgentSeek lifecycle spec.",
            "deepagents/content-builder": (
                "DeepAgents content builder with skills, subagents, image generation, "
                "streamed UI, and AgentSeek lifecycle spec."
            ),
            "deepagents/default": "Local create_deep_agent runnable with AgentSeek lifecycle spec.",
            "deepagents/research": (
                "DeepAgents research agent with Tavily search, streamed tool/sub-agent UI, "
                "and AgentSeek lifecycle spec."
            ),
            "deepagents/sandbox": ("DeepAgents sandbox coding agent with streamed UI and AgentSeek lifecycle spec."),
            "langchain/agentic-rag": (
                "LangChain agentic RAG with OceanBase vector search and AgentSeek lifecycle spec."
            ),
            "langchain/agentic-rag-hybrid": (
                "LangChain agentic hybrid RAG with image ingestion, vector/sparse/full-text/metadata search, "
                "comparison demos, optional Phoenix observability, and AgentSeek lifecycle spec."
            ),
            "langchain/agentic-rag-openvino": (
                "LangChain local RAG with OpenVINO models and AgentSeek lifecycle spec."
            ),
            "langchain/cli-remote": (
                "Remote LangGraph CLI agent bridged through LangGraphClientRunnable with AgentSeek lifecycle spec."
            ),
            "langchain/default": ("LangChain create_agent plus CopilotKit middleware with AgentSeek lifecycle spec."),
            "langchain/markdown-messages": (
                "LangChain create_agent and react-markdown frontend with AgentSeek lifecycle spec."
            ),
        },
        "template_digests": {
            "bub/default": "096c35aeff1cfe3b3420bb5d9ba5a8473c959fa535380b3822f1fb9044b50dfa",
            "deepagents/content-builder": "0239ac0ebb0632369d9b3f86b33b5fb3ab9c153a752f94a5ddcaf8d82c091b34",
            "deepagents/default": "3d0b41f4af8b18ea236d11f166803c524784fa5605d18d13c5d6b310d1b47118",
            "deepagents/research": "7a0ae249636015c2e1d91cbc42dffcb278bae757aff2a7f928711ad534ff4ca0",
            "deepagents/sandbox": "b532af922546232aa7500f774342b957eb644e25faef26a7aca5a5c9d5773fa4",
            "langchain/agentic-rag": "133635986878f88ebf16964eee05d10d298053420c432c6ef9fa30a1b7e6fdc9",
            "langchain/agentic-rag-hybrid": ("64c83a6d99cd1c9b916cd39f81eb24cf5424efaf26a266d57d71d61c89c239df"),
            "langchain/agentic-rag-openvino": ("ae7227904fa2341d0698c64adf5350869867ee4947b1a9ebd08e1a871b94d3e5"),
            "langchain/cli-remote": "9667e628548f60cd688d6fda6bb4a37fa726712459ed97761ce2442fbf564826",
            "langchain/default": "befb5541f39993bfde0938c3ec90f47693efe16d72cab505cdf2d4d5757b7d31",
            "langchain/markdown-messages": ("6a08b10cc113252bea0db5545554ebec41f27e962ed9f1475800ab518485c622"),
        },
    }


def test_lock_digest_uses_the_exact_packaged_bytes() -> None:
    """Changing insignificant JSON whitespace must change cache identity."""
    from agentseek.cli.catalog import parse_catalog_lock

    raw = files("agentseek").joinpath("data/catalog-lock.json").read_bytes()
    parsed = parse_catalog_lock(raw)

    assert parsed.digest == hashlib.sha256(raw).hexdigest()
    assert parse_catalog_lock(raw + b"\n").digest != parsed.digest


def test_template_tree_digest_is_unambiguous_across_file_boundaries(tmp_path: Path) -> None:
    """File boundaries must be part of the trusted subtree encoding."""
    from agentseek.cli.catalog import _template_tree_digest

    single = tmp_path / "single"
    split = tmp_path / "split"
    single.mkdir()
    split.mkdir()
    boundary = len(b"b").to_bytes(8, "big") + b"b"
    (single / "a").write_bytes(boundary + b"content")
    (split / "a").write_bytes(b"")
    (split / "b").write_bytes(b"content")

    assert _template_tree_digest(single) != _template_tree_digest(split)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", True),
        ("lifecycle_version", 1),
        ("catalog_commit", "main"),
        ("core_commit", "883ADDAD1E2993C4BE6FC8BA053F87F25FB5057A"),
        ("catalog_repository", "http://github.com/agentseek-ai/agentseek-templates.git"),
        ("templates_root", "../templates"),
        ("index_path", "/templates/index.json"),
        ("templates", {"../escape": "unsafe"}),
        ("template_digests", {"bub/default": "0" * 64}),
    ],
)
def test_catalog_lock_rejects_malformed_coordinates(field: str, value: object) -> None:
    """Malformed packaged coordinates must fail instead of selecting another source."""
    from agentseek.cli.catalog import CatalogError, parse_catalog_lock

    lock = json.loads(files("agentseek").joinpath("data/catalog-lock.json").read_bytes())
    lock[field] = value

    with pytest.raises(CatalogError):
        parse_catalog_lock(json.dumps(lock).encode())


def test_catalog_lock_rejects_malformed_template_digest() -> None:
    """Trusted template digests must be canonical lowercase SHA-256 values."""
    from agentseek.cli.catalog import CatalogError, parse_catalog_lock

    lock = json.loads(files("agentseek").joinpath("data/catalog-lock.json").read_bytes())
    lock["template_digests"]["bub/default"] = "A" * 64

    with pytest.raises(CatalogError, match="lowercase SHA-256"):
        parse_catalog_lock(json.dumps(lock).encode())


def test_catalog_lock_rejects_unknown_schema_fields() -> None:
    """Schema-one clients must not silently reinterpret a newer lock shape."""
    from agentseek.cli.catalog import CatalogError, parse_catalog_lock

    lock = json.loads(files("agentseek").joinpath("data/catalog-lock.json").read_bytes())
    lock["fallback_repository"] = "https://github.com/ob-labs/agentseek.git"

    with pytest.raises(CatalogError):
        parse_catalog_lock(json.dumps(lock).encode())


def test_locked_template_is_published_once_and_reused_offline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A complete exact-coordinate cache must satisfy later offline creates."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = _catalog_archive(lock)
    fetches = 0

    def fetch(_: catalog.CatalogLock, destination: Path) -> None:
        nonlocal fetches
        fetches += 1
        destination.write_bytes(archive)

    monkeypatch.setattr(catalog, "_download_archive", fetch)

    first = catalog.prepare_locked_template(lock, "bub/default", tmp_path)
    second = catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert first == second
    assert fetches == 1
    assert (first / "cookiecutter.json").is_file()
    assert (first / "{{cookiecutter.project_slug}}" / "README.md").read_text(encoding="utf-8") == "# Demo\n"
    assert not (first.parents[1] / "langchain" / "default").exists()


def test_archive_registry_must_equal_the_embedded_snapshot(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A template may not be combined with a registry from another revision."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = _catalog_archive(lock, index={"bub/default": "Different registry."})
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))

    with pytest.raises(catalog.CatalogError, match="registry"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []


def test_downloaded_template_must_match_the_trusted_embedded_digest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An exact-coordinate archive still fails closed when its template bytes drift."""
    from agentseek.cli import catalog

    fixture_lock = _fixture_lock(catalog.load_catalog_lock())
    mismatched_lock = replace(
        fixture_lock,
        template_digests={**fixture_lock.template_digests, "bub/default": "0" * 64},
    )
    archive = _catalog_archive(fixture_lock)
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))

    with pytest.raises(catalog.CatalogError, match="embedded digest"):
        catalog.prepare_locked_template(mismatched_lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []


@pytest.mark.parametrize("mutation", ["empty-directory", "executable-file"])
def test_downloaded_template_digest_covers_semantic_tree_entries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    mutation: str,
) -> None:
    """Empty directories and executable semantics are part of the trusted tree."""
    from agentseek.cli import catalog

    if mutation == "executable-file" and os.name == "nt":
        pytest.skip("Windows does not preserve POSIX executable bits in extracted test archives")

    lock = _fixture_lock(catalog.load_catalog_lock())
    extras: list[tuple[tarfile.TarInfo, bytes | None]] = []
    readme_mode = 0o644
    if mutation == "empty-directory":
        directory = tarfile.TarInfo(
            "agentseek-templates-fixture/templates/bub/default/{{cookiecutter.project_slug}}/injected-empty"
        )
        directory.type = tarfile.DIRTYPE
        extras.append((directory, None))
    else:
        readme_mode = 0o755
    archive = _catalog_archive(lock, extras=extras, readme_mode=readme_mode)
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))

    with pytest.raises(catalog.CatalogError, match="embedded digest"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)


def test_warm_cache_cannot_forge_directory_or_executable_semantics(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Metadata cannot authorize added directories or executable source files."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = _catalog_archive(lock)
    fetches = 0

    def fetch(_: catalog.CatalogLock, destination: Path) -> None:
        nonlocal fetches
        fetches += 1
        destination.write_bytes(archive)

    monkeypatch.setattr(catalog, "_download_archive", fetch)
    template = catalog.prepare_locked_template(lock, "bub/default", tmp_path)
    injected = template / "{{cookiecutter.project_slug}}" / "injected-empty"
    injected.mkdir()
    readme = template / "{{cookiecutter.project_slug}}" / "README.md"
    if os.name != "nt":
        readme.chmod(0o755)
    metadata_path = next(tmp_path.rglob(".agentseek-catalog-metadata.json"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["template_sha256"] = catalog._template_tree_digest(template)
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    repaired = catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert fetches == 2
    assert not (repaired / "{{cookiecutter.project_slug}}" / "injected-empty").exists()
    assert ((repaired / "{{cookiecutter.project_slug}}" / "README.md").stat().st_mode & 0o111) == 0


class _FakeArchiveResponse:
    def __init__(
        self,
        payload: bytes,
        *,
        content_length: int | None = None,
        content_encoding: str | None = None,
        status_error: Exception | None = None,
    ) -> None:
        self.payload = payload
        self.headers = {} if content_length is None else {"content-length": str(content_length)}
        if content_encoding is not None:
            self.headers["content-encoding"] = content_encoding
        self.status_error = status_error

    def raise_for_status(self) -> None:
        if self.status_error is not None:
            raise self.status_error

    def iter_raw(self) -> object:
        midpoint = max(1, len(self.payload) // 2)
        yield self.payload[:midpoint]
        yield self.payload[midpoint:]


class _FakeStreamContext:
    def __init__(self, response: _FakeArchiveResponse) -> None:
        self.response = response

    def __enter__(self) -> _FakeArchiveResponse:
        return self.response

    def __exit__(self, *args: object) -> None:
        return None


class _FailingStreamContext:
    def __enter__(self) -> None:
        raise httpx.ConnectError("offline")

    def __exit__(self, *args: object) -> None:
        return None


def test_download_uses_exact_github_commit_and_raw_bytes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The network request must never resolve a release tag or mutable branch."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    payload = b"raw archive bytes"
    captured: dict[str, object] = {}

    def stream(method: str, url: str, **kwargs: object) -> _FakeStreamContext:
        captured.update(method=method, url=url, **kwargs)
        return _FakeStreamContext(_FakeArchiveResponse(payload, content_length=len(payload)))

    monkeypatch.setattr(catalog.httpx, "stream", stream)
    destination = tmp_path / "catalog.tar.gz"

    catalog._download_archive(lock, destination)

    assert destination.read_bytes() == payload
    assert captured["method"] == "GET"
    assert captured["url"] == (
        "https://codeload.github.com/agentseek-ai/agentseek-templates/tar.gz/494863bc1b9aab19f9885d716c03ce654fb26014"
    )
    assert captured["follow_redirects"] is False


def test_download_connect_failure_is_normalized_without_double_closing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A stream-open error must remain a CatalogError and clean its temporary file."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    monkeypatch.setattr(catalog.httpx, "stream", lambda *_args, **_kwargs: _FailingStreamContext())
    destination = tmp_path / "catalog.tar.gz"

    with pytest.raises(catalog.CatalogError, match="download failed"):
        catalog._download_archive(lock, destination)

    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("advertise_size", [True, False], ids=["content-length", "streamed-bytes"])
def test_download_rejects_compressed_archives_over_the_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    advertise_size: bool,
) -> None:
    """Both declared and actual response sizes must enforce the compressed cap."""
    from agentseek.cli import catalog

    payload = b"12345"
    response = _FakeArchiveResponse(payload, content_length=len(payload) if advertise_size else None)
    monkeypatch.setattr(catalog, "MAX_COMPRESSED_BYTES", 4)
    monkeypatch.setattr(catalog.httpx, "stream", lambda *args, **kwargs: _FakeStreamContext(response))
    destination = tmp_path / "catalog.tar.gz"

    with pytest.raises(catalog.CatalogError, match="64 MiB compressed limit"):
        catalog._download_archive(catalog.load_catalog_lock(), destination)

    assert not destination.exists()


def test_download_rejects_unexpected_http_content_encoding(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Raw response bytes are usable only when the server honors identity encoding."""
    from agentseek.cli import catalog

    response = _FakeArchiveResponse(b"encoded", content_encoding="gzip")
    monkeypatch.setattr(catalog.httpx, "stream", lambda *args, **kwargs: _FakeStreamContext(response))
    destination = tmp_path / "catalog.tar.gz"

    with pytest.raises(catalog.CatalogError, match="Content-Encoding"):
        catalog._download_archive(catalog.load_catalog_lock(), destination)

    assert not destination.exists()


def test_download_enforces_an_overall_deadline_and_removes_partial_bytes(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Per-read progress must not allow an archive transfer to run forever."""
    from agentseek.cli import catalog

    response = _FakeArchiveResponse(b"two chunks")
    monotonic_values = iter([0.0, 121.0])
    monkeypatch.setattr(catalog.time, "monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr(catalog.httpx, "stream", lambda *args, **kwargs: _FakeStreamContext(response))
    destination = tmp_path / "catalog.tar.gz"

    with pytest.raises(catalog.CatalogError, match="overall timeout"):
        catalog._download_archive(catalog.load_catalog_lock(), destination)

    assert not destination.exists()


@pytest.mark.parametrize(
    "name",
    [
        "/absolute/file",
        "agentseek-templates-fixture/../escape",
        "C:/windows/escape",
        "agentseek-templates-fixture\\..\\escape",
        "agentseek-templates-fixture/control\x1b",
        "agentseek-templates-fixture//duplicate-separator",
        "agentseek-templates-fixture/templates/bub/CON/file",
        "agentseek-templates-fixture/templates/bub/trailing./file",
        "agentseek-templates-fixture/templates/bub/trailing /file",
        "agentseek-templates-fixture/templates/bub/colon:name/file",
    ],
    ids=[
        "posix-absolute",
        "traversal",
        "windows-drive",
        "backslash-traversal",
        "control",
        "duplicate-separator",
        "windows-reserved",
        "trailing-dot",
        "trailing-space",
        "windows-colon",
    ],
)
def test_archive_rejects_unsafe_paths_after_the_selected_template(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    name: str,
) -> None:
    """A bad later member must prevent an otherwise valid template publication."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    member = tarfile.TarInfo(name)
    member.size = 1
    archive = _catalog_archive(lock, extras=[(member, b"x")])
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))

    with pytest.raises(catalog.CatalogError, match="unsafe path"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []


@pytest.mark.parametrize(
    "member_type",
    [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.BLKTYPE, tarfile.FIFOTYPE],
    ids=["symlink", "hardlink", "character-device", "block-device", "fifo"],
)
def test_archive_rejects_links_and_special_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    member_type: bytes,
) -> None:
    """Downloaded archives may contain only directories and regular files."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    member = tarfile.TarInfo("agentseek-templates-fixture/unsafe")
    member.type = member_type
    member.linkname = "../../outside"
    archive = _catalog_archive(lock, extras=[(member, None)])
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))

    with pytest.raises(catalog.CatalogError, match="link or device"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []


def test_archive_rejects_duplicate_and_multiple_root_members(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Ambiguous archive namespaces must not be mapped into one cache tree."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    duplicates = tarfile.TarInfo("agentseek-templates-fixture/templates/index.json")
    duplicate_bytes = json.dumps(dict(lock.templates)).encode()
    duplicates.size = len(duplicate_bytes)
    other_root = tarfile.TarInfo("different-root/file")
    other_root.size = 1

    for expected, extra in [
        ("duplicate paths", (duplicates, duplicate_bytes)),
        ("multiple repository roots", (other_root, b"x")),
    ]:
        archive = _catalog_archive(lock, extras=[extra])
        monkeypatch.setattr(
            catalog,
            "_download_archive",
            lambda _lock, destination, payload=archive: destination.write_bytes(payload),
        )
        isolated_cache = tmp_path / expected.replace(" ", "-")
        with pytest.raises(catalog.CatalogError, match=expected):
            catalog.prepare_locked_template(lock, "bub/default", isolated_cache)
        assert list(isolated_cache.rglob(".agentseek-catalog-metadata.json")) == []


@pytest.mark.parametrize(
    ("constant", "limit", "message"),
    [
        ("MAX_ARCHIVE_MEMBERS", 3, "10,000 member limit"),
        ("MAX_MEMBER_BYTES", 10, "32 MiB member limit"),
        ("MAX_TOTAL_UNCOMPRESSED_BYTES", 10, "256 MiB uncompressed limit"),
    ],
    ids=["member-count", "single-member", "total-uncompressed"],
)
def test_archive_enforces_all_declared_size_and_member_limits(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    constant: str,
    limit: int,
    message: str,
) -> None:
    """Limits apply to the whole archive, including unselected subtrees."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    monkeypatch.setattr(catalog, constant, limit)
    archive = _catalog_archive(lock)
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))

    with pytest.raises(catalog.CatalogError, match=message):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []


def test_archive_counts_hidden_pax_payload_toward_uncompressed_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """PAX extension records consumed by tarfile must not bypass the archive budget."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    member = tarfile.TarInfo("agentseek-templates-fixture/extra")
    member.size = 1
    member.pax_headers = {"comment": "x" * 100_000}
    archive = _catalog_archive(lock, extras=[(member, b"x")])
    monkeypatch.setattr(catalog, "MAX_TOTAL_UNCOMPRESSED_BYTES", 4096)
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))

    with pytest.raises(catalog.CatalogError, match="256 MiB uncompressed limit"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []


def test_archive_counts_hidden_pax_payload_toward_member_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Hidden extension records must obey the same per-member cap as files."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    member = tarfile.TarInfo("agentseek-templates-fixture/extra")
    member.size = 1
    member.pax_headers = {"comment": "x" * 100_000}
    archive = _catalog_archive(lock, extras=[(member, b"x")])
    monkeypatch.setattr(catalog, "MAX_MEMBER_BYTES", 4096)
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))

    with pytest.raises(catalog.CatalogError, match="32 MiB member limit"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []
    assert list(tmp_path.rglob("catalog.tar")) == []


def test_archive_counts_hidden_pax_headers_toward_member_count(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The raw-member limit must include extension headers hidden by tarfile."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    member = tarfile.TarInfo("agentseek-templates-fixture/extra")
    member.size = 1
    member.pax_headers = {"comment": "metadata"}
    archive = _catalog_archive(lock, extras=[(member, b"x")])
    monkeypatch.setattr(catalog, "MAX_ARCHIVE_MEMBERS", 5)
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))

    with pytest.raises(catalog.CatalogError, match="10,000 member limit"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []


def test_archive_rejects_deep_extension_header_chains(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Nested extension parsing must stop well before Python's recursion limit."""
    from agentseek.cli import catalog

    def pax_record(key: str, value: str) -> bytes:
        body = f"{key}={value}\n".encode()
        length = len(body) + 2
        while True:
            record = f"{length} ".encode() + body
            if len(record) == length:
                return record
            length = len(record)

    lock = _fixture_lock(catalog.load_catalog_lock())
    extras: list[tuple[tarfile.TarInfo, bytes | None]] = []
    for index in range(2):
        content = pax_record("comment", str(index))
        header = tarfile.TarInfo(f"pax-{index}")
        header.type = tarfile.XGLTYPE
        header.size = len(content)
        extras.append((header, content))
    member = tarfile.TarInfo("agentseek-templates-fixture/extra")
    member.size = 1
    extras.append((member, b"x"))
    archive = _catalog_archive(lock, extras=extras)
    monkeypatch.setattr(catalog, "MAX_EXTENSION_DEPTH", 1, raising=False)
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))

    with pytest.raises(catalog.CatalogError, match="extension nesting limit"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []


def test_truncated_archive_is_never_published(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A transport-complete but structurally truncated tarball must not become reusable."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = _catalog_archive(lock)
    monkeypatch.setattr(
        catalog,
        "_download_archive",
        lambda _lock, destination: destination.write_bytes(archive[: len(archive) // 2]),
    )

    with pytest.raises(catalog.CatalogError, match="invalid or truncated"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []


def test_corrupt_deflate_stream_is_reported_as_catalog_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Low-level decompressor errors must not escape the catalog boundary."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = bytearray(gzip.compress(bytes(range(256)) * 1000))
    archive[10] ^= 0xFF
    monkeypatch.setattr(
        catalog,
        "_download_archive",
        lambda _lock, destination: destination.write_bytes(archive),
    )

    with pytest.raises(catalog.CatalogError, match="invalid or truncated"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert list(tmp_path.rglob(".agentseek-catalog-metadata.json")) == []
    assert list(tmp_path.rglob("catalog.tar")) == []


@pytest.mark.parametrize(
    "damage",
    [
        "metadata-repository",
        "metadata-commit",
        "metadata-key",
        "metadata-lock",
        "configuration",
        "content",
        "content-and-metadata",
    ],
    ids=[
        "wrong-repository",
        "wrong-commit",
        "wrong-key",
        "wrong-lock-digest",
        "partial",
        "corrupt",
        "forged-content-digest",
    ],
)
def test_invalid_cache_entries_are_replaced_from_the_exact_archive(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    damage: str,
) -> None:
    """Wrong, partial, and corrupt cache entries must never be warm-cache hits."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = _catalog_archive(lock)
    fetches = 0

    def fetch(_: catalog.CatalogLock, destination: Path) -> None:
        nonlocal fetches
        fetches += 1
        destination.write_bytes(archive)

    monkeypatch.setattr(catalog, "_download_archive", fetch)
    template = catalog.prepare_locked_template(lock, "bub/default", tmp_path)
    if damage.startswith("metadata-"):
        metadata_path = next(tmp_path.rglob(".agentseek-catalog-metadata.json"))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        field = {
            "metadata-repository": "catalog_repository",
            "metadata-commit": "catalog_commit",
            "metadata-key": "template_key",
            "metadata-lock": "catalog_lock_sha256",
        }[damage]
        metadata[field] = "wrong"
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    elif damage == "configuration":
        (template / "cookiecutter.json").unlink()
    elif damage == "content":
        (template / "{{cookiecutter.project_slug}}" / "README.md").write_text("tampered\n", encoding="utf-8")
    else:
        (template / "{{cookiecutter.project_slug}}" / "README.md").write_text("tampered\n", encoding="utf-8")
        metadata_path = next(tmp_path.rglob(".agentseek-catalog-metadata.json"))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["template_sha256"] = catalog._template_tree_digest(template)
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    repaired = catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert fetches == 2
    assert (repaired / "{{cookiecutter.project_slug}}" / "README.md").read_text(encoding="utf-8") == "# Demo\n"
    assert all(".stale-" not in path.name for path in tmp_path.rglob("*"))


def test_stale_cleanup_failure_does_not_hide_a_valid_replacement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Cleanup is best-effort after a valid candidate becomes authoritative."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = _catalog_archive(lock)
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))
    template = catalog.prepare_locked_template(lock, "bub/default", tmp_path)
    (template / "{{cookiecutter.project_slug}}" / "README.md").write_text("tampered\n", encoding="utf-8")
    monkeypatch.setattr(
        catalog,
        "_remove_stale_entry",
        lambda *_args: (_ for _ in ()).throw(catalog.CatalogError("cleanup unavailable")),
    )

    repaired = catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert (repaired / "{{cookiecutter.project_slug}}" / "README.md").read_text(encoding="utf-8") == "# Demo\n"
    assert catalog._validated_cache(repaired.parents[2], lock, "bub/default") == repaired


def test_invalid_cache_plus_network_failure_does_not_reuse_stale_content(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Offline reuse is allowed only for a currently valid exact-coordinate cache."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = _catalog_archive(lock)
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))
    template = catalog.prepare_locked_template(lock, "bub/default", tmp_path)
    (template / "cookiecutter.json").write_text("{", encoding="utf-8")
    monkeypatch.setattr(
        catalog,
        "_download_archive",
        lambda *args, **kwargs: (_ for _ in ()).throw(catalog.CatalogError("network unavailable")),
    )

    with pytest.raises(catalog.CatalogError, match="network unavailable"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert (template / "cookiecutter.json").read_text(encoding="utf-8") == "{"


def test_cache_identity_includes_repository_commit_key_and_raw_lock_digest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """No coordinate component may alias another catalog cache entry."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    variants = [
        lock,
        replace(lock, catalog_repository="https://github.com/agentseek-ai/other-catalog.git"),
        replace(lock, catalog_commit="0123456789abcdef0123456789abcdef01234567"),
        _fixture_lock(catalog.parse_catalog_lock(lock.raw + b"\n")),
    ]
    archives = [_catalog_archive(variant, key="bub/default") for variant in variants] + [
        _catalog_archive(lock, key="langchain/default")
    ]
    fetches = 0

    def fetch(_: catalog.CatalogLock, destination: Path) -> None:
        nonlocal fetches
        destination.write_bytes(archives[fetches])
        fetches += 1

    monkeypatch.setattr(catalog, "_download_archive", fetch)
    paths = [catalog.prepare_locked_template(variant, "bub/default", tmp_path) for variant in variants]
    paths.append(catalog.prepare_locked_template(lock, "langchain/default", tmp_path))

    assert fetches == 5
    assert len(set(paths)) == 5


def test_link_like_cache_entry_is_rejected_without_fetching(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A cache-coordinate symlink must not be renamed, followed, or overwritten."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    lock_dir, cache_entry, _ = catalog._cache_layout(tmp_path, lock, "bub/default")
    outside = tmp_path / "outside"
    outside.mkdir()
    cache_entry.symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(
        catalog,
        "_download_archive",
        lambda *args, **kwargs: pytest.fail("unsafe cache state must fail before network access"),
    )

    with pytest.raises(catalog.CatalogError, match="link-like"):
        catalog.prepare_locked_template(lock, "bub/default", tmp_path)

    assert cache_entry.is_symlink()
    assert lock_dir in cache_entry.parents


def test_concurrent_publishers_download_once_and_share_the_atomic_entry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A second process waiting on the coordinate lock must reuse the first publication."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = _catalog_archive(lock)
    started = Event()
    release = Event()
    fetches = 0

    def fetch(_: catalog.CatalogLock, destination: Path) -> None:
        nonlocal fetches
        fetches += 1
        started.set()
        assert release.wait(timeout=5)
        destination.write_bytes(archive)

    monkeypatch.setattr(catalog, "_download_archive", fetch)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(catalog.prepare_locked_template, lock, "bub/default", tmp_path)
        assert started.wait(timeout=5)
        second = executor.submit(catalog.prepare_locked_template, lock, "bub/default", tmp_path)
        release.set()
        paths = [first.result(timeout=5), second.result(timeout=5)]

    assert fetches == 1
    assert paths[0] == paths[1]
    assert (paths[0] / "cookiecutter.json").is_file()


def test_default_listing_is_offline_and_ignores_the_core_checkout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Named default discovery must use only the embedded standalone snapshot."""
    from agentseek.cli import catalog

    monkeypatch.setattr(
        create_module,
        "_local_templates_root",
        lambda: pytest.fail("the frozen core template mirror must be ignored"),
    )
    monkeypatch.setattr(
        catalog,
        "_download_archive",
        lambda *args, **kwargs: pytest.fail("listing must not access the network"),
    )

    result = CliRunner().invoke(build_command_app(), ["create", "--list-templates", "--filter", "markdown"])

    assert result.exit_code == 0, result.output
    assert "langchain/markdown-messages" in result.output
    assert "bub/default" not in result.output


def test_unknown_default_template_fails_before_archive_download(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unregistered key must be rejected using the embedded snapshot alone."""
    from agentseek.cli import catalog

    monkeypatch.setattr(
        create_module,
        "_local_templates_root",
        lambda: pytest.fail("the frozen core template mirror must be ignored"),
    )
    monkeypatch.setattr(
        catalog,
        "_download_archive",
        lambda *args, **kwargs: pytest.fail("an unknown key must not trigger a download"),
    )

    result = CliRunner().invoke(build_command_app(), ["create", "bub/not-published", "--describe"])

    assert result.exit_code == 2
    assert "Template bub/not-published was not found" in result.output
    assert "bub/default" in result.output


def test_named_default_create_uses_locked_template_and_core_source_pair(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Catalog coordinates must never replace generated-project core dependencies."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = _catalog_archive(lock)
    cookiecutters_dir = tmp_path / "cookiecutters"
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        "cookiecutter.config.get_user_config",
        lambda: {"cookiecutters_dir": str(cookiecutters_dir)},
    )
    monkeypatch.setattr(catalog, "load_catalog_lock", lambda: lock)
    monkeypatch.setattr(catalog, "_download_archive", lambda _lock, destination: destination.write_bytes(archive))
    monkeypatch.setattr(
        create_module,
        "_local_templates_root",
        lambda: pytest.fail("the frozen core template mirror must be ignored"),
    )

    def run(source: TemplateSource, *, output_dir: Path, no_input: bool) -> None:
        captured["source"] = source
        captured["context"] = create_module._cookiecutter_source_context(source)

    monkeypatch.setattr(create_module, "_run_cookiecutter", run)
    result = CliRunner().invoke(
        build_command_app(),
        ["create", "bub/default", "--no-input", "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert Path(source.template).is_relative_to(cookiecutters_dir)
    assert captured["context"] == {
        "_agentseek_source_path": "",
        "_agentseek_source_path_posix": "",
        "_agentseek_source_path_shell": "",
        "_agentseek_source_url": "https://github.com/ob-labs/agentseek.git",
        "_agentseek_source_ref": "883addad1e2993c4be6fc8ba053f87f25fb5057a",
    }


def test_interactive_choices_come_from_the_lock_before_network_access(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Both interactive menus must finish from the snapshot before materialization."""
    from agentseek.cli import catalog

    lock = _fixture_lock(catalog.load_catalog_lock())
    archive = _catalog_archive(lock, key="langchain/markdown-messages")
    responses = iter(["langchain", "markdown-messages"])
    events: list[str] = []

    def prompt(*args: object, **kwargs: object) -> str:
        events.append("prompt")
        return next(responses)

    def download(_: catalog.CatalogLock, destination: Path) -> None:
        events.append("download")
        destination.write_bytes(archive)

    def run(*args: object, **kwargs: object) -> None:
        events.append("run")

    monkeypatch.setattr(create_module.typer, "prompt", prompt)
    monkeypatch.setattr(catalog, "load_catalog_lock", lambda: lock)
    monkeypatch.setattr(catalog, "_download_archive", download)
    monkeypatch.setattr(create_module, "_run_cookiecutter", run)
    monkeypatch.setattr(
        "cookiecutter.config.get_user_config",
        lambda: {"cookiecutters_dir": str(tmp_path / "cookiecutters")},
    )

    result = CliRunner().invoke(build_command_app(), ["create"])

    assert result.exit_code == 0, result.output
    assert events == ["prompt", "prompt", "download", "run"]
    assert "markdown-messages" in result.output


def test_invalid_packaged_lock_fails_without_legacy_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    """A broken wheel lock must be an explicit error, never a route to v1 or mutable main."""
    from agentseek.cli import catalog

    monkeypatch.setattr(catalog, "load_catalog_lock", lambda: (_ for _ in ()).throw(catalog.CatalogError("bad lock")))
    monkeypatch.setattr(
        create_module,
        "_local_templates_root",
        lambda: pytest.fail("a bad lock must not fall back to local core templates"),
    )
    monkeypatch.setattr(
        "cookiecutter.vcs.clone",
        lambda *args, **kwargs: pytest.fail("a bad lock must not fall back to Cookiecutter clone"),
    )

    result = CliRunner().invoke(build_command_app(), ["create", "bub/default", "--no-input"])

    assert result.exit_code == 1
    assert result.output.strip() == "Could not load the locked template catalog: bad lock."


def test_locked_archive_failure_never_falls_back_to_core_or_cookiecutter_clone(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A cold-cache network failure must remain an explicit locked-catalog error."""
    from agentseek.cli import catalog

    monkeypatch.setattr(
        "cookiecutter.config.get_user_config",
        lambda: {"cookiecutters_dir": str(tmp_path / "cookiecutters")},
    )
    monkeypatch.setattr(
        catalog,
        "_download_archive",
        lambda *args, **kwargs: (_ for _ in ()).throw(catalog.CatalogError("network unavailable")),
    )
    monkeypatch.setattr(
        create_module,
        "_local_templates_root",
        lambda: pytest.fail("locked failure must not inspect the core template mirror"),
    )
    monkeypatch.setattr(
        "cookiecutter.vcs.clone",
        lambda *args, **kwargs: pytest.fail("locked failure must not use legacy clone fallback"),
    )
    monkeypatch.setattr(
        create_module,
        "_run_cookiecutter",
        lambda *args, **kwargs: pytest.fail("locked failure must not generate"),
    )

    result = CliRunner().invoke(build_command_app(), ["create", "bub/default", "--no-input"])

    assert result.exit_code == 1
    assert result.output.strip() == "Could not prepare the locked template catalog: network unavailable."


def test_unexpected_locked_cache_failure_is_generic_and_secret_safe(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Unexpected filesystem failures must remain explicit without leaking internals."""
    from agentseek.cli import catalog

    monkeypatch.setattr(
        "cookiecutter.config.get_user_config",
        lambda: {"cookiecutters_dir": str(tmp_path / "cookiecutters")},
    )
    monkeypatch.setattr(
        catalog,
        "prepare_locked_template",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("secret-cache-detail")),
    )

    result = CliRunner().invoke(build_command_app(), ["create", "bub/default", "--no-input"])

    assert result.exit_code == 1
    assert result.output.strip() == "Could not prepare the locked template catalog."
    assert "secret-cache-detail" not in result.output


def test_positional_passthrough_does_not_load_the_default_lock(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Direct Cookiecutter sources remain independent of bundled catalog health."""
    from agentseek.cli import catalog

    captured: dict[str, object] = {}
    monkeypatch.setattr(
        catalog,
        "load_catalog_lock",
        lambda: pytest.fail("positional passthrough must not read the default lock"),
    )

    def run(source: TemplateSource, **kwargs: object) -> None:
        captured["source"] = source

    monkeypatch.setattr(create_module, "_run_cookiecutter", run)
    template = tmp_path / "template"
    template.mkdir()

    result = CliRunner().invoke(build_command_app(), ["create", str(template), "--checkout", "dev"])

    assert result.exit_code == 0, result.output
    source = captured["source"]
    assert isinstance(source, TemplateSource)
    assert source.template == str(template)
    assert source.checkout == "dev"


def test_standalone_checkout_ref_resolves_to_one_exact_commit(monkeypatch: pytest.MonkeyPatch) -> None:
    """A developer branch override must become an immutable cache coordinate first."""
    completed = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="0123456789abcdef0123456789abcdef01234567\trefs/heads/release/next\n",
        stderr="",
    )
    calls: list[tuple[list[str], dict[str, object]]] = []

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append((command, kwargs))
        return completed

    monkeypatch.setattr(create_module.subprocess, "run", run)

    commit = create_module._resolve_standalone_catalog_ref(
        "https://github.com/agentseek-ai/agentseek-templates.git",
        "release/next",
    )

    assert commit == "0123456789abcdef0123456789abcdef01234567"
    assert calls[0][0] == [
        "git",
        "ls-remote",
        "--exit-code",
        "--",
        "https://github.com/agentseek-ai/agentseek-templates.git",
        "refs/heads/release/next",
        "refs/tags/release/next",
        "refs/tags/release/next^{}",
    ]
    assert calls[0][1]["timeout"] == create_module.EXPLICIT_CATALOG_GIT_TIMEOUT_SECONDS


def test_standalone_checkout_rejects_ambiguous_branch_and_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    """A ref naming both a branch and tag must not silently choose one."""
    stdout = (
        "0123456789abcdef0123456789abcdef01234567\trefs/heads/release\n"
        "89abcdef0123456789abcdef0123456789abcdef\trefs/tags/release\n"
    )
    monkeypatch.setattr(
        create_module.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args=[], returncode=0, stdout=stdout, stderr=""),
    )

    with pytest.raises(create_module._InvalidExplicitCatalog, match="ambiguous"):
        create_module._resolve_standalone_catalog_ref(
            "https://github.com/agentseek-ai/agentseek-templates.git",
            "release",
        )


def test_checkout_override_uses_registry_and_files_from_the_resolved_commit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """The embedded registry must not be mixed with a developer-override checkout."""
    templates_root = tmp_path / "override" / "templates"
    template_dir = templates_root / "bub" / "dev"
    (template_dir / "{{cookiecutter.project_slug}}").mkdir(parents=True)
    (template_dir / "cookiecutter.json").write_text('{"project_slug":"demo"}', encoding="utf-8")
    (template_dir / "{{cookiecutter.project_slug}}" / "README.md").write_text("dev\n", encoding="utf-8")
    prepared = create_module._prepared_catalog(
        templates_root,
        {"bub/dev": "Developer override."},
        source_policy="explicit",
    )
    coordinate: dict[str, create_module._ExplicitCatalogCoordinate] = {}
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        create_module,
        "_resolve_standalone_catalog_ref",
        lambda repository, ref: "0123456789abcdef0123456789abcdef01234567",
    )

    def prepare(value: create_module._ExplicitCatalogCoordinate) -> create_module._PreparedCatalog:
        coordinate["value"] = value
        return prepared

    monkeypatch.setattr(create_module, "_prepare_explicit_catalog", prepare)

    def run(source: TemplateSource, **kwargs: object) -> None:
        captured["source"] = source
        captured["context"] = create_module._cookiecutter_source_context(source)

    monkeypatch.setattr(create_module, "_run_cookiecutter", run)
    list_result = CliRunner().invoke(
        build_command_app(),
        ["create", "bub", "--list-templates", "--checkout", "release/next"],
    )
    create_result = CliRunner().invoke(
        build_command_app(),
        ["create", "bub/dev", "--checkout", "release/next", "--no-input"],
    )

    assert list_result.exit_code == 0, list_result.output
    assert create_result.exit_code == 0, create_result.output
    assert "bub/dev" in list_result.output
    assert "bub/default" not in list_result.output
    assert coordinate["value"].commit == "0123456789abcdef0123456789abcdef01234567"
    assert captured["context"] == {
        "_agentseek_source_path": "",
        "_agentseek_source_path_posix": "",
        "_agentseek_source_path_shell": "",
        "_agentseek_source_url": "https://github.com/ob-labs/agentseek.git",
        "_agentseek_source_ref": "883addad1e2993c4be6fc8ba053f87f25fb5057a",
    }


def test_checkout_override_registry_is_not_filtered_by_the_legacy_core_quarantine() -> None:
    """A standalone development checkout owns its registry independently of the v1 mirror."""
    from agentseek.cli import catalog

    prepared = create_module._prepared_catalog(
        None,
        {"bub/contextseek": "Reviewed standalone template."},
        source_policy="checkout-override",
        catalog_lock=catalog.load_catalog_lock(),
    )

    assert create_module._list_templates("bub", prepared) == ["contextseek"]
    assert create_module._catalog_has_template(prepared, "bub", "contextseek") is True
