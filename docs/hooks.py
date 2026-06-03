from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

HUB_TEMPLATE_CONTEXT = {
    "en": {
        "locale": "en",
        "title": "Hub",
        "summary": "Contrib packages and skills that live in this repository, plus Bub.",
        "intro_kicker": "$ repo hub",
        "intro_body": "Jump to each contrib README or <code>SKILL.md</code> in this repository. Bub is kept here as the runtime entry point.",
        "search_placeholder": "Search contrib packages, skills, and Bub...",
        "all_label": "All",
        "showing_label": "Showing",
        "of_label": "of",
        "items_label": "items",
        "empty_label": "No items match the current filter.",
        "entry_point_label": "Entry point",
        "path_label": "Path",
        "install_command_label": "Install command",
        "copy_label": "Copy",
        "copied_label": "Copied",
        "readme_label": "README",
        "skill_doc_label": "SKILL.md",
        "category_labels": {
            "Plugins": "Plugins",
            "Skills": "Skills",
            "Friends": "Friends",
        },
        "badge_labels": {
            "plugin": "plugin",
            "skill": "skill",
            "bundled": "bundled",
            "local": "local",
            "friend": "friend",
        },
    },
    "zh": {
        "locale": "zh",
        "title": "目录",
        "summary": "这里收录本仓库内的 contrib 包、skills，以及 Bub。",
        "intro_kicker": "$ repo hub",
        "intro_body": "从这里快速跳到本仓库内的 contrib README 或 <code>SKILL.md</code>。Bub 作为 runtime 入口保留在这里。",
        "search_placeholder": "搜索 contrib 包、skills 和 Bub...",
        "all_label": "全部",
        "showing_label": "显示",
        "of_label": "/",
        "items_label": "项",
        "empty_label": "当前筛选条件下没有匹配项。",
        "entry_point_label": "入口点",
        "path_label": "路径",
        "install_command_label": "安装命令",
        "copy_label": "复制",
        "copied_label": "已复制",
        "readme_label": "README",
        "skill_doc_label": "SKILL.md",
        "category_labels": {
            "Plugins": "插件",
            "Skills": "技能",
            "Friends": "生态项目",
        },
        "badge_labels": {
            "plugin": "插件",
            "skill": "技能",
            "bundled": "内置",
            "local": "本地",
            "friend": "生态",
        },
    },
}


def _render_hub_page(docs_dir: Path) -> None:
    data_path = docs_dir / "_data" / "hub.yml"
    template_dir = docs_dir / "_templates"

    data = yaml.safe_load(data_path.read_text(encoding="utf-8")) or {}
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("hub.md.j2")
    categories = data.get("categories", [])

    for locale, context in HUB_TEMPLATE_CONTEXT.items():
        output_path = docs_dir / ("hub.md" if locale == "en" else f"hub.{locale}.md")
        rendered = template.render(categories=categories, ui=context)
        output_path.write_text(rendered.rstrip() + "\n", encoding="utf-8")


def on_config(config, **kwargs):
    docs_dir = Path(config["docs_dir"])
    _render_hub_page(docs_dir)
    return config
