"""Regression checks for the localized root README diagram assets."""

from __future__ import annotations

import re
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "diagram" / "agentseek-readme"
SVG_NS = "{http://www.w3.org/2000/svg}"
IMMUTABLE_ASSET_ROOT = "https://raw.githubusercontent.com/ob-labs/agentseek/v0.1.1/diagram/agentseek-readme/"

SVG_ASSETS = {
    "architecture-en": ASSET_ROOT / "agentseek-architecture-en.svg",
    "architecture-zh": ASSET_ROOT / "agentseek-architecture-zh.svg",
    "adlc-en": ASSET_ROOT / "agentseek-adlc-en.svg",
    "adlc-zh": ASSET_ROOT / "agentseek-adlc-zh.svg",
}

PNG_ASSETS = {name: path.with_name(f"{path.stem}@2x.png") for name, path in SVG_ASSETS.items()}

REQUIRED_LABELS = {
    "architecture-en": (
        "Developer",
        "Coding agent",
        "Desktop client",
        "Stable AgentSeek CLI",
        "create · info",
        "task · doctor · dev",
        "Locked versioned catalog",
        "Fully editable generated project",
        "Lifecycle contract",
        "Project-owned runtime & integrations",
        "Native LangGraph backend",
        "React frontend",
        "Bub",
        "Models · Tools · MCP",
        "External services",
        "Observability · lifecycle signals",
    ),
    "architecture-zh": (
        "开发者",
        "编码智能体",
        "桌面客户端",
        "稳定的 AgentSeek CLI",
        "create · info",
        "task · doctor · dev",
        "锁定的版本化模板目录",
        "完全可编辑的生成项目",
        "生命周期契约",
        "项目自有运行时与集成",
        "原生 LangGraph 后端",
        "React 前端",
        "Bub",
        "模型 · 工具 · MCP",
        "外部服务",
        "可观测性 · 生命周期信号",
    ),
    "adlc-en": (
        "Discover",
        "Create",
        "Inspect",
        "Configure",
        "Check",
        "Run",
        "Observe",
        "Iterate",
        "Templates · Discover + Create",
        "Observability · Inspect through Iterate",
        "Return to Inspect · keep the project",
    ),
    "adlc-zh": (
        "发现",
        "创建",
        "审视",
        "配置",
        "检查",
        "运行",
        "观测",
        "迭代",
        "模板 · 发现 + 创建",
        "可观测性 · 从审视贯穿迭代",
        "返回审视 · 继续使用现有项目",
    ),
}

PROHIBITED_ASSET_CLAIMS = (
    "seekdb",
    "agentseek api",
    "langgraph-dev",
    "sync-langgraph",
    "frontend-dev",
)

GEOMETRY_ATTRIBUTES = (
    "id",
    "class",
    "data-role",
    "data-from",
    "data-to",
    "data-span",
    "x",
    "y",
    "x1",
    "y1",
    "x2",
    "y2",
    "cx",
    "cy",
    "r",
    "rx",
    "ry",
    "width",
    "height",
    "points",
    "d",
    "transform",
    "marker-start",
    "marker-end",
)


def _parse_svg(path: Path) -> ET.Element:
    assert path.is_file(), path
    return ET.parse(path).getroot()  # noqa: S314 - only trusted checked-in SVG assets are parsed


def _visible_text(root: ET.Element) -> str:
    return " ".join(part.strip() for part in root.itertext() if part.strip())


def _geometry_signature(root: ET.Element) -> tuple[tuple[object, ...], ...]:
    """Return language-independent structure and geometry in paint order."""
    signature: list[tuple[object, ...]] = []
    for element in root.iter():
        tag = element.tag.removeprefix(SVG_NS)
        if tag in {"style", "title", "desc", "text", "tspan"}:
            continue
        attributes = tuple((name, element.attrib[name]) for name in GEOMETRY_ATTRIBUTES if name in element.attrib)
        signature.append((tag, attributes))
    return tuple(signature)


def _png_chunks(path: Path) -> list[tuple[bytes, bytes]]:
    """Parse and validate every chunk in a complete PNG file."""
    content = path.read_bytes()
    assert content.startswith(b"\x89PNG\r\n\x1a\n"), path

    chunks: list[tuple[bytes, bytes]] = []
    offset = 8
    while True:
        assert offset + 8 <= len(content), f"{path}: truncated PNG chunk header"
        length = struct.unpack(">I", content[offset : offset + 4])[0]
        chunk_type = content[offset + 4 : offset + 8]
        chunk_end = offset + 12 + length
        assert chunk_end <= len(content), f"{path}: truncated {chunk_type!r} chunk"

        data = content[offset + 8 : offset + 8 + length]
        stored_crc = struct.unpack(">I", content[offset + 8 + length : chunk_end])[0]
        expected_crc = zlib.crc32(data, zlib.crc32(chunk_type)) & 0xFFFFFFFF
        assert stored_crc == expected_crc, f"{path}: invalid {chunk_type!r} CRC"
        chunks.append((chunk_type, data))
        offset = chunk_end

        if chunk_type == b"IEND":
            assert not data, f"{path}: IEND chunk must be empty"
            assert offset == len(content), f"{path}: trailing bytes after IEND"
            return chunks


@pytest.mark.parametrize("name", SVG_ASSETS)
def test_svg_assets_are_responsive_parseable_and_localized(name: str) -> None:
    path = SVG_ASSETS[name]
    root = _parse_svg(path)

    assert root.tag == f"{SVG_NS}svg", path
    assert root.attrib.get("viewBox") == "0 0 1280 720", path
    assert "width" not in root.attrib, path
    assert "height" not in root.attrib, path
    assert root.attrib.get("role") == "img", path

    titles = root.findall(f"{SVG_NS}title")
    descriptions = root.findall(f"{SVG_NS}desc")
    assert len(titles) == 1 and (titles[0].text or "").strip(), path
    assert len(descriptions) == 1 and (descriptions[0].text or "").strip(), path
    labelled_by = root.attrib.get("aria-labelledby", "").split()
    assert labelled_by == [titles[0].attrib.get("id"), descriptions[0].attrib.get("id")], path

    visible_text = _visible_text(root)
    for label in REQUIRED_LABELS[name]:
        assert label in visible_text, (path, label)


@pytest.mark.parametrize("name", SVG_ASSETS)
def test_svg_assets_exclude_inspiration_and_future_runtime_claims(name: str) -> None:
    content = SVG_ASSETS[name].read_text(encoding="utf-8").lower()

    for claim in PROHIBITED_ASSET_CLAIMS:
        assert claim not in content, (SVG_ASSETS[name], claim)


@pytest.mark.parametrize("name", PNG_ASSETS)
def test_png_fallbacks_are_valid_exact_2x_renders(name: str) -> None:
    path = PNG_ASSETS[name]
    assert path.is_file(), path

    chunks = _png_chunks(path)
    chunk_types = [chunk_type for chunk_type, _data in chunks]
    assert b"IHDR" in chunk_types, path
    assert b"IDAT" in chunk_types, path
    assert b"IEND" in chunk_types, path

    ihdr_chunks = [data for chunk_type, data in chunks if chunk_type == b"IHDR"]
    assert len(ihdr_chunks) == 1, path
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", ihdr_chunks[0])
    assert (width, height) == (2560, 1440), path
    assert (bit_depth, color_type, compression, filtering, interlace) == (8, 6, 0, 0, 0), path

    compressed = b"".join(data for chunk_type, data in chunks if chunk_type == b"IDAT")
    scanlines = zlib.decompress(compressed)
    assert len(scanlines) == height * (1 + width * 4), path


@pytest.mark.parametrize(
    ("readme", "expected_filenames"),
    (
        (ROOT / "README.md", ("agentseek-architecture-en.svg", "agentseek-adlc-en.svg")),
        (ROOT / "README.zh.md", ("agentseek-architecture-zh.svg", "agentseek-adlc-zh.svg")),
    ),
)
def test_root_readme_images_use_immutable_release_urls_and_map_to_local_assets(
    readme: Path,
    expected_filenames: tuple[str, str],
) -> None:
    text = readme.read_text(encoding="utf-8")
    release_images = [
        target for target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text) if target.startswith(IMMUTABLE_ASSET_ROOT)
    ]

    assert release_images == [f"{IMMUTABLE_ASSET_ROOT}{filename}" for filename in expected_filenames], readme
    for target in release_images:
        local_asset = ASSET_ROOT / target.removeprefix(IMMUTABLE_ASSET_ROOT)
        assert local_asset.is_file(), (readme, target)


@pytest.mark.parametrize("stem", ("architecture", "adlc"))
def test_localized_pairs_keep_identical_geometry_and_semantics(stem: str) -> None:
    english = _parse_svg(SVG_ASSETS[f"{stem}-en"])
    chinese = _parse_svg(SVG_ASSETS[f"{stem}-zh"])

    assert _geometry_signature(english) == _geometry_signature(chinese)


def test_architecture_preserves_ownership_flow_and_cross_cutting_observability() -> None:
    root = _parse_svg(SVG_ASSETS["architecture-en"])
    expected_flow = (
        ("actors-to-cli", "actors", "agentseek-cli"),
        ("cli-to-catalog", "agentseek-cli", "template-catalog"),
        ("catalog-to-project", "template-catalog", "generated-project"),
        ("project-to-runtime", "generated-project", "project-runtime"),
    )

    for path_id, source, target in expected_flow:
        connector = root.find(f".//*[@id='{path_id}']")
        assert connector is not None, path_id
        assert connector.attrib.get("data-from") == source
        assert connector.attrib.get("data-to") == target
        assert connector.attrib.get("marker-end") == "url(#arrow-cyan)"

    observability = root.find(".//*[@id='observability-band']")
    assert observability is not None
    assert observability.attrib.get("data-span") == "agentseek-cli template-catalog generated-project project-runtime"


def test_adlc_return_lands_on_inspect_and_bands_cover_the_declared_stages() -> None:
    root = _parse_svg(SVG_ASSETS["adlc-en"])
    stage_ids = ("discover", "create", "inspect", "configure", "check", "run", "observe", "iterate")

    for stage_id in stage_ids:
        assert root.find(f".//*[@id='{stage_id}']") is not None, stage_id

    loop_return = root.find(".//*[@id='iterate-to-inspect']")
    assert loop_return is not None
    assert loop_return.attrib.get("data-from") == "iterate"
    assert loop_return.attrib.get("data-to") == "inspect"
    assert loop_return.attrib.get("marker-end") == "url(#arrow-emerald)"

    template_band = root.find(".//*[@id='templates-band']")
    observability_band = root.find(".//*[@id='observability-band']")
    assert template_band is not None
    assert template_band.attrib.get("data-span") == "discover create"
    assert observability_band is not None
    assert observability_band.attrib.get("data-span") == "inspect configure check run observe iterate"
