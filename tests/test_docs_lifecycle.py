"""Documentation regression checks for lifecycle task guidance."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from agentseek.cli.lifecycle.compatibility import MINIMUM_AGENTSEEK_API_VERSION

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_ROOT = ROOT / "templates"
TEMPLATE_INDEX = TEMPLATES_ROOT / "index.json"
LIFECYCLE_REFERENCES = (
    ROOT / "docs" / "reference" / "lifecycle-spec.md",
    ROOT / "docs" / "reference" / "lifecycle-spec.zh.md",
)
LIFECYCLE_SNAPSHOT_SUMMARIES = (
    ROOT / "docs" / "get-started" / "index.md",
    ROOT / "docs" / "get-started" / "index.zh.md",
    ROOT / "docs" / "reference" / "template-authoring-contract.md",
    ROOT / "docs" / "reference" / "template-authoring-contract.zh.md",
    *LIFECYCLE_REFERENCES,
)
LIFECYCLE_V2_SPEC_URL = "https://github.com/ob-labs/agentseek/blob/main/specs/lifecycle-v2-service-discovery.md"
ROOT_DOTENV_EXAMPLE = ROOT / ".env.example"
ROOT_READMES = (
    ROOT / "README.md",
    ROOT / "README.zh.md",
)
IMMUTABLE_ASSET_ROOT = "https://raw.githubusercontent.com/ob-labs/agentseek/v0.1.1/diagram/agentseek-readme/"
CONTRIBUTING_GUIDE_URL = "https://github.com/ob-labs/agentseek/blob/HEAD/CONTRIBUTING.md"
README_BANNER_TARGETS = (
    "https://github.com/ob-labs/agentseek/stargazers",
    "https://github.com/ob-labs/agentseek/releases",
    "https://pypi.org/project/agentseek/",
    "https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain",
    "https://github.com/ob-labs/agentseek/graphs/contributors",
    "https://github.com/ob-labs/agentseek/issues",
    "https://github.com/ob-labs/agentseek/blob/HEAD/LICENSE",
    "https://ob-labs.github.io/agentseek/",
)
README_HERO_BADGE_PAIRS = (
    (
        "https://github.com/ob-labs/agentseek/stargazers",
        "https://img.shields.io/github/stars/ob-labs/agentseek?style=flat-square&logo=github",
    ),
    (
        "https://github.com/ob-labs/agentseek/releases",
        "https://img.shields.io/github/v/release/ob-labs/agentseek?style=flat-square",
    ),
    ("https://pypi.org/project/agentseek/", "https://img.shields.io/pypi/v/agentseek?style=flat-square&logo=pypi"),
    (
        "https://pypi.org/project/agentseek/",
        "https://img.shields.io/pypi/pyversions/agentseek?style=flat-square&logo=python",
    ),
    (
        "https://github.com/ob-labs/agentseek/actions/workflows/main.yml?query=branch%3Amain",
        "https://img.shields.io/github/actions/workflow/status/ob-labs/agentseek/main.yml?branch=main&style=flat-square&label=CI",
    ),
    (
        "https://github.com/ob-labs/agentseek/graphs/contributors",
        "https://img.shields.io/github/contributors/ob-labs/agentseek?style=flat-square",
    ),
    (
        "https://github.com/ob-labs/agentseek/issues",
        "https://img.shields.io/github/issues/ob-labs/agentseek?style=flat-square",
    ),
    (
        "https://github.com/ob-labs/agentseek/blob/HEAD/LICENSE",
        "https://img.shields.io/github/license/ob-labs/agentseek?style=flat-square",
    ),
    (
        "https://ob-labs.github.io/agentseek/",
        "https://img.shields.io/badge/docs-AgentSeek-0ea5e9?style=flat-square",
    ),
)
README_COMMUNITY_DOCS_TARGETS = {
    "README.md": "https://ob-labs.github.io/agentseek/",
    "README.zh.md": "https://ob-labs.github.io/agentseek/zh/",
}
README_CONTRIBUTION_CTA_ALTS = {
    "README.md": "Contribute to AgentSeek",
    "README.zh.md": "为 AgentSeek 贡献",
}
README_ANCHORS = (
    "experience-adlc",
    "what-is-agentseek",
    "agent-development-lifecycle",
    "guided-templates",
    "community",
    "development",
)

CANONICAL_RESEARCH_WALKTHROUGH = (
    "uv tool install agentseek",
    "agentseek create deepagents/research --no-input",
    "cd research_deepagent",
    "agentseek info",
    "cp .env.example .env",
    "cp frontend/.env.example frontend/.env",
    "$EDITOR .env",
    "agentseek task --list",
    "agentseek task sync",
    "agentseek task frontend",
    "agentseek doctor",
    "agentseek dev --dry-run",
    "agentseek dev",
    "agentseek doctor --live",
)

README_SECTION_MARKERS = {
    "README.md": (
        "## Experience the local ADLC",
        "## What is AgentSeek?",
        "## Agent Development Lifecycle",
        "## Observability throughout the loop",
        "## Guided templates",
        "## Core concepts and commands",
        "## Documentation",
        "## 🌐 Next Steps & Community",
        "## 🛠️ Development",
        "### Contributing",
        "## 📄 License",
    ),
    "README.zh.md": (
        "## 体验本地 ADLC",
        "## 什么是 AgentSeek？",  # noqa: RUF001 - exact localized heading
        "## Agent 开发生命周期",
        "## 贯穿全流程的可观测性",
        "## 引导式模板",
        "## 核心概念与命令",
        "## 文档",
        "## 🌐 下一步与社区",
        "## 🛠️ 开发",
        "### 贡献",
        "## 📄 许可证",
    ),
}

README_STAR_HISTORY_TEXT = {
    "README.md": ("Star History",),
    "README.zh.md": ("Star 历史",),
}

README_REQUIRED_TEXT = {
    "README.md": (
        "AgentSeek 0.1.3",
        "releases/tag/v0.1.3",
        "native LangGraph backend",
        "React frontend",
        "agentseek info --json",
        "AGENTSEEK_CONSOLE=true",
        "LangSmith",
        "agentseek create --list-templates",
        "agentseek create --list-templates --filter deepagents",
        "agentseek create deepagents/research --describe",
        f"{IMMUTABLE_ASSET_ROOT}agentseek-architecture-en.svg",
        f"{IMMUTABLE_ASSET_ROOT}agentseek-adlc-en.svg",
    ),
    "README.zh.md": (
        "AgentSeek 0.1.3",
        "releases/tag/v0.1.3",
        "发现、创建、审视、配置、检查、运行、观测和迭代",
        "原生 LangGraph 后端",
        "React 前端",
        "agentseek info --json",
        "AGENTSEEK_CONSOLE=true",
        "LangSmith",
        "agentseek create --list-templates",
        "agentseek create --list-templates --filter deepagents",
        "agentseek create deepagents/research --describe",
        f"{IMMUTABLE_ASSET_ROOT}agentseek-architecture-zh.svg",
        f"{IMMUTABLE_ASSET_ROOT}agentseek-adlc-zh.svg",
    ),
}

README_LIVE_DOCTOR_COMMENTS = {
    "README.md": "# In another terminal, after agentseek dev starts, check live services.",
    "README.zh.md": "# agentseek dev 启动后，在另一个终端中检查实时服务。",  # noqa: RUF001
}


def _bash_commands(text: str) -> list[str]:
    """Return non-comment command lines from fenced bash examples."""
    commands: list[str] = []
    for block in re.findall(r"```bash\n(.*?)```", text, flags=re.DOTALL):
        commands.extend(
            line.strip() for line in block.splitlines() if line.strip() and not line.lstrip().startswith("#")
        )
    return commands


def _hero_badges_html(text: str) -> str:
    """Return the linked-badge block from the centered README hero."""
    hero_start = text.index('<div align="center">')
    heading_end = text.index("</h1>", hero_start)
    badges_start = text.index("<p>\n", heading_end)
    badges_end = text.index("</p>", badges_start)

    return text[badges_start:badges_end]


def _hero_badge_pairs(text: str) -> list[tuple[str, str]]:
    """Extract the ordered linked badge images from the centered README hero."""
    badges = _hero_badges_html(text)

    return re.findall(r'<a href="([^"]+)"><img alt="[^"]+" src="([^"]+)" /></a>', badges)


def _community_section(text: str) -> str:
    """Return the localized community block before the development separator."""
    community_start = text.index('<a id="community"></a>')
    development_separator = text.index("\n---\n", community_start)

    return text[community_start:development_separator]


def _public_template_readmes() -> list[Path]:
    registry = json.loads(TEMPLATE_INDEX.read_text(encoding="utf-8"))
    readmes: list[Path] = []
    for key in sorted(registry):
        template_dir = TEMPLATES_ROOT / key
        for readme in [
            template_dir / "README.md",
            template_dir / "{{cookiecutter.project_slug}}" / "README.md",
        ]:
            if readme.is_file():
                readmes.append(readme)
    return readmes


def test_quickstarts_prefer_lifecycle_tasks_over_raw_setup_commands() -> None:
    """Public quickstarts should route setup through AgentSeek lifecycle tasks."""
    docs = [
        ROOT / "README.md",
        ROOT / "README.zh.md",
        ROOT / "docs" / "index.md",
        ROOT / "docs" / "index.zh.md",
        ROOT / "docs" / "get-started" / "index.md",
        ROOT / "docs" / "get-started" / "index.zh.md",
        *_public_template_readmes(),
    ]

    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        assert "uv sync" not in text, doc
        assert "npm install --prefix frontend" not in text, doc


def test_core_quickstarts_show_lifecycle_task_discovery() -> None:
    """Main quickstarts should show task discovery after project creation."""
    docs = [
        ROOT / "README.md",
        ROOT / "README.zh.md",
        ROOT / "docs" / "index.md",
        ROOT / "docs" / "index.zh.md",
        ROOT / "docs" / "get-started" / "index.md",
        ROOT / "docs" / "get-started" / "index.zh.md",
    ]

    for doc in docs:
        assert "agentseek task" in doc.read_text(encoding="utf-8"), doc


@pytest.mark.parametrize("readme", ROOT_READMES)
def test_root_readmes_keep_the_current_research_walkthrough_in_order(readme: Path) -> None:
    """The root walkthrough must follow the shipped research lifecycle exactly."""
    commands = _bash_commands(readme.read_text(encoding="utf-8"))
    positions = [commands.index(command) for command in CANONICAL_RESEARCH_WALKTHROUGH]

    assert positions == sorted(positions), readme


@pytest.mark.parametrize("readme", ROOT_READMES)
def test_root_readmes_explain_that_live_checks_run_in_another_terminal(readme: Path) -> None:
    """The blocking dev command must not hide how to run the following live check."""
    text = readme.read_text(encoding="utf-8")
    expected = f"agentseek dev\n{README_LIVE_DOCTOR_COMMENTS[readme.name]}\nagentseek doctor --live"

    assert expected in text, readme


@pytest.mark.parametrize("readme", ROOT_READMES)
def test_root_readmes_keep_localized_adlc_structure_and_current_runtime_truth(readme: Path) -> None:
    """Both landing pages describe the same current local ADLC without future claims."""
    text = readme.read_text(encoding="utf-8")
    markers = README_SECTION_MARKERS[readme.name]
    positions = [text.index(marker) for marker in markers]

    assert positions == sorted(positions), readme
    for required in README_REQUIRED_TEXT[readme.name]:
        assert required in text, (readme, required)

    assert "AgentSeek API" not in text, readme
    assert "langgraph-dev" not in text, readme
    assert "sync-langgraph" not in text, readme
    assert "frontend-dev" not in text, readme
    assert "agentseek task observability" not in text, readme
    assert not re.search(r"seekdb", text, flags=re.IGNORECASE), readme


@pytest.mark.parametrize("readme", ROOT_READMES)
def test_root_readmes_keep_the_shared_banner_contract(readme: Path) -> None:
    """Both landing pages expose the same AgentSeek hero entry points."""
    text = readme.read_text(encoding="utf-8")
    badge_pairs = _hero_badge_pairs(text)

    assert text.startswith('<div align="center">'), readme
    assert "oceanbase/seekdb" not in text, readme
    assert badge_pairs == list(README_HERO_BADGE_PAIRS), readme
    assert len(badge_pairs) == 9, readme
    assert all("style=flat-square" in source for _target, source in badge_pairs), readme
    assert {target for target, _source in badge_pairs} == set(README_BANNER_TARGETS), readme
    for anchor in README_ANCHORS:
        assert f'<a id="{anchor}"></a>' in text, (readme, anchor)
        assert f"](#{anchor})" in text, (readme, anchor)


@pytest.mark.parametrize("readme", ROOT_READMES)
def test_root_readmes_keep_contributor_wall_without_star_history(readme: Path) -> None:
    """Contribution sections must show contributors without a Star History embed."""
    text = readme.read_text(encoding="utf-8")
    contributor_wall = re.search(
        r'<a href="https://github\.com/ob-labs/agentseek/graphs/contributors">'
        r'<img alt="[^"]+" src="https://contrib\.rocks/image\?repo=ob-labs/agentseek&max=400" /></a>',
        text,
    )

    assert contributor_wall is not None, readme
    assert "star-history.com" not in text, readme
    for forbidden in README_STAR_HISTORY_TEXT[readme.name]:
        assert forbidden not in text, (readme, forbidden)


def test_root_readme_heroes_keep_matching_badge_targets_and_images() -> None:
    """Language variants must keep an identical ordered linked-badge contract."""
    english_badges, chinese_badges = (_hero_badge_pairs(readme.read_text(encoding="utf-8")) for readme in ROOT_READMES)

    assert english_badges == chinese_badges
    assert {target for target, _source in english_badges} == {target for target, _source in chinese_badges}
    assert {source for _target, source in english_badges} == {source for _target, source in chinese_badges}


@pytest.mark.parametrize("readme", ROOT_READMES)
def test_root_readme_heroes_split_badges_into_balanced_rows(readme: Path) -> None:
    """The badge strip must render as an intentional five-plus-four layout."""
    badge_rows = _hero_badges_html(readme.read_text(encoding="utf-8")).split("<br />")

    assert [row.count('<a href="') for row in badge_rows] == [5, 4], readme


@pytest.mark.parametrize("readme", ROOT_READMES)
def test_root_readmes_keep_localized_community_routes_and_contribution_cta(readme: Path) -> None:
    """Community routes must send readers to docs, issues, and contribution instructions."""
    community = _community_section(readme.read_text(encoding="utf-8"))
    contribution_cta = re.search(
        rf'<a href="([^"]+)"><img alt="{re.escape(README_CONTRIBUTION_CTA_ALTS[readme.name])}"',
        community,
    )

    assert README_COMMUNITY_DOCS_TARGETS[readme.name] in community, readme
    assert "https://github.com/ob-labs/agentseek/issues" in community, readme
    assert CONTRIBUTING_GUIDE_URL in community, readme
    assert contribution_cta is not None, readme
    assert contribution_cta.group(1) == CONTRIBUTING_GUIDE_URL, readme


def test_root_dotenv_example_matches_runtime_alias_contract() -> None:
    """The root example must not promise dotenv values become Bub aliases."""
    text = ROOT_DOTENV_EXAMPLE.read_text(encoding="utf-8")

    assert "AGENTSEEK_* variables are passed through to Bub as BUB_* aliases." not in text
    assert "does not create `BUB_*` aliases" in text
    assert "launching process environment" in text


@pytest.mark.parametrize("reference", LIFECYCLE_REFERENCES)
def test_lifecycle_references_describe_authored_v2_loading(reference: Path) -> None:
    """Both references must describe the shipped authored v1/v2 boundary."""
    text = reference.read_text(encoding="utf-8")
    table_rows = [line for line in text.splitlines() if line.startswith("|")]

    assert LIFECYCLE_V2_SPEC_URL in text, reference
    assert "lifecycle-v2-service-discovery.md" in text, reference
    assert any("`1`, `2`" in row for row in table_rows), reference
    assert any("`templates/`" in row and "`version = 1`" in row for row in table_rows), reference
    has_v2_catalog_row = any(
        "`agentseek-ai/agentseek-templates`" in row and "`version = 2`" in row for row in table_rows
    )
    assert has_v2_catalog_row, reference


@pytest.mark.parametrize(
    "guide",
    (ROOT / "docs" / "guides" / "choose-template.md", ROOT / "docs" / "guides" / "choose-template.zh.md"),
)
def test_choose_template_guides_match_locked_catalog_runtime(guide: Path) -> None:
    """The guides must describe the lifecycle command shipped by the locked catalog."""
    text = guide.read_text(encoding="utf-8")

    assert "langgraph dev" in text, guide
    assert "agentseek-api dev" not in text, guide


@pytest.mark.parametrize(
    "reference",
    (
        *LIFECYCLE_REFERENCES,
        ROOT / "src" / "skills" / "agentseek-lifecycle" / "references" / "agentseek-lifecycle.md",
    ),
)
def test_lifecycle_references_define_the_immutable_environment_boundary(reference: Path) -> None:
    """Lifecycle references must describe the one-time child environment contract."""
    text = reference.read_text(encoding="utf-8")
    lines = text.splitlines()

    assert "immutable snapshot" in text
    assert "`KEY=`" in text
    assert "`KEY`" in text
    assert "malformed dotenv" in text
    assert "exit 2" in text
    assert "`agentseek info`" in text
    assert "`agentseek doctor --strict`" in text
    assert "exit 1" in text
    if reference.name.endswith(".zh.md"):
        assert "非 dry-run" in text
        assert "dotenv 状态" in text
        assert "物理绑定出现的顺序" in text
        assert "已捕获的启动环境" in text
        assert "初始子进程环境/快照" in text
        assert "任意子进程代码" in text
    else:
        assert "non-dry-run" in text
        assert "dotenv status" in text
        assert "physical bindings in order" in text
        assert "captured launch environment" in text
        assert "initial child environment/snapshot" in text
        assert "arbitrary child code" in text.lower()
    assert f"`agentseek-api >= {MINIMUM_AGENTSEEK_API_VERSION}`" in text
    assert any("`agentseek dev`" in line and "snapshot" in line for line in lines)
    assert any("`agentseek task`" in line and "`env_file`" in line for line in lines)
    assert "multiple env files, or env interpolation." not in text
    assert "多个 env 文件或 env 插值" not in text


@pytest.mark.parametrize(
    "reference",
    (
        ROOT / "docs" / "guides" / "create-template.md",
        ROOT / "docs" / "guides" / "create-template.zh.md",
        ROOT / "docs" / "reference" / "template-authoring-contract.md",
        ROOT / "docs" / "reference" / "template-authoring-contract.zh.md",
    ),
)
def test_template_authoring_requires_a_compatible_released_api(reference: Path) -> None:
    """Template authors must pin a released runtime API with direct process argv."""
    text = reference.read_text(encoding="utf-8")

    assert f"`agentseek-api >= {MINIMUM_AGENTSEEK_API_VERSION}`" in text
    assert "exact published version" in text
    assert "direct argv" in text


@pytest.mark.parametrize(
    ("guide", "former_generic_guidance"),
    (
        (
            ROOT / "docs" / "guides" / "create-template.md",
            "During `agentseek dev`, the\n"
            "project `.env` is also passed to long-running child processes, with exported\n"
            "shell variables taking precedence.",
        ),
        (
            ROOT / "docs" / "guides" / "create-template.zh.md",
            "在 lifecycle 文件的 `[env.*]` 中声明同一组必需名称。AgentSeek 用这些声明检查\n"
            "就绪状态\uff1b`agentseek dev` 会把项目 `.env` 传给长运行子进程\uff0cshell 变量优先。",
        ),
    ),
)
def test_template_guides_define_the_one_time_dev_environment_boundary(
    guide: Path,
    former_generic_guidance: str,
) -> None:
    """Template guides must not describe dotenv as a generic child pass-through."""
    text = guide.read_text(encoding="utf-8")

    assert "immutable snapshot" in text
    assert "`KEY=`" in text
    assert "`agentseek task`" in text
    assert "`env_file`" in text
    assert former_generic_guidance not in text


@pytest.mark.parametrize("reference", LIFECYCLE_SNAPSHOT_SUMMARIES)
def test_lifecycle_snapshot_summaries_explicitly_exclude_dry_run(reference: Path) -> None:
    """Every public snapshot summary must reserve resolution for non-dry-run dev."""
    text = reference.read_text(encoding="utf-8")
    qualification = "非 dry-run" if reference.name.endswith(".zh.md") else "non-dry-run"

    assert qualification in text
    assert "`agentseek dev`" in text
    if reference in LIFECYCLE_REFERENCES:
        env_file_row = next(line for line in text.splitlines() if line.startswith("| `env_file`"))

        assert qualification in env_file_row
        assert "`agentseek dev`" in env_file_row


@pytest.mark.parametrize(
    "reference",
    (
        ROOT / "docs" / "guides" / "create-template.zh.md",
        ROOT / "docs" / "reference" / "template-authoring-contract.zh.md",
    ),
)
def test_chinese_template_authoring_localizes_release_contract_terms(reference: Path) -> None:
    """Chinese authoring guidance keeps only the required English contract phrases."""
    text = reference.read_text(encoding="utf-8")

    assert "\uff08immutable snapshot\uff09" in text
    assert "\uff08exact published version\uff09" in text
    assert "\uff08direct argv\uff09" in text
    assert "editable" not in text
    assert "checkout" not in text
    assert re.search(r"\bpin\b", text) is None
    assert "digest" not in text


@pytest.mark.parametrize(
    "reference",
    (
        ROOT / "docs" / "get-started" / "index.zh.md",
        ROOT / "docs" / "guides" / "create-template.zh.md",
        ROOT / "docs" / "reference" / "lifecycle-spec.zh.md",
        ROOT / "docs" / "reference" / "template-authoring-contract.zh.md",
    ),
)
def test_chinese_lifecycle_docs_do_not_code_switch_nonmandatory_parenthetical_terms(reference: Path) -> None:
    """Chinese lifecycle prose keeps only the required English contract parentheticals."""
    text = reference.read_text(encoding="utf-8")

    for term in (
        "\uff08non-dry-run\uff09",
        "\uff08captured launch environment\uff09",
        "\uff08physical bindings in order\uff09",
        "\uff08initial child environment/snapshot\uff09",
        "\uff08arbitrary child code\uff09",
        "\uff08dotenv status\uff09",
    ):
        assert term not in text
