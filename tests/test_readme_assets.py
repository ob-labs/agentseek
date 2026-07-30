"""Regression checks for the localized root README diagram assets."""

from __future__ import annotations

import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "diagram" / "agentseek-readme"
SVG_NS = "{http://www.w3.org/2000/svg}"

SVG_ASSETS = {
    "architecture-en": ASSET_ROOT / "agentseek-architecture-en.svg",
    "architecture-zh": ASSET_ROOT / "agentseek-architecture-zh.svg",
    "adlc-en": ASSET_ROOT / "agentseek-adlc-en.svg",
    "adlc-zh": ASSET_ROOT / "agentseek-adlc-zh.svg",
}

PNG_ASSETS = {
    name: path.with_name(f"{path.stem}@2x.png") for name, path in SVG_ASSETS.items()
}

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
    return ET.parse(path).getroot()


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


@pytest.mark.parametrize("name", SVG_ASSETS)
def test_svg_assets_are_responsive_parseable_and_localized(name: str) -> None:
    path = SVG_ASSETS[name]
    root = _parse_svg(path)

    assert root.tag == f"{SVG_NS}svg", path
    assert root.attrib.get("viewBox") == "0 0 1280 720", path
    assert "width" not in root.attrib, path
    assert "height" not in root.attrib, path

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

    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n", path
    assert header[12:16] == b"IHDR", path
    assert struct.unpack(">II", header[16:24]) == (2560, 1440), path


@pytest.mark.parametrize("readme", (ROOT / "README.md", ROOT / "README.zh.md"))
def test_root_readme_local_images_exist(readme: Path) -> None:
    text = readme.read_text(encoding="utf-8")
    local_images = [
        target
        for target in re.findall(r"!\[[^\]]*\]\(([^)]+)\)", text)
        if "://" not in target
    ]

    assert len(local_images) == 2, readme
    for target in local_images:
        assert (ROOT / target).is_file(), (readme, target)


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
