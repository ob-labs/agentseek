"""Documentation regression checks for lifecycle task guidance."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_ROOT = ROOT / "templates"
TEMPLATE_INDEX = TEMPLATES_ROOT / "index.json"
LIFECYCLE_REFERENCES = (
    ROOT / "docs" / "reference" / "lifecycle-spec.md",
    ROOT / "docs" / "reference" / "lifecycle-spec.zh.md",
)
LIFECYCLE_V2_SPEC_URL = "https://github.com/ob-labs/agentseek/blob/main/specs/lifecycle-v2-service-discovery.md"
ROOT_DOTENV_EXAMPLE = ROOT / ".env.example"
ROOT_READMES = (
    ROOT / "README.md",
    ROOT / "README.zh.md",
)
IMMUTABLE_ASSET_ROOT = "https://raw.githubusercontent.com/ob-labs/agentseek/v0.1.1/diagram/agentseek-readme/"

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
        "## Development",
        "## Community and course",
        "## License",
    ),
    "README.zh.md": (
        "## 体验本地 ADLC",
        "## 什么是 AgentSeek？",  # noqa: RUF001 - exact localized heading
        "## Agent 开发生命周期",
        "## 贯穿全流程的可观测性",
        "## 引导式模板",
        "## 核心概念与命令",
        "## 文档",
        "## 开发",
        "## 社区与课程",
        "## License",
    ),
}

README_REQUIRED_TEXT = {
    "README.md": (
        "AgentSeek 0.1.1",
        "releases/tag/v0.1.0",
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
        "AgentSeek 0.1.1",
        "releases/tag/v0.1.0",
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
