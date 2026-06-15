from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

HUB_TEMPLATE_CONTEXT = {
    "en": {
        "locale": "en",
        "title": "Hub",
        "summary": "Plugins, skills, and a few ecosystem links that live in or next to this repository.",
        "intro_kicker": "$ repo hub",
        "intro_body": 'Jump to each README or <code>SKILL.md</code>. For the wider Bub ecosystem, see <a href="https://hub.bub.build">hub.bub.build</a>.',
        "search_placeholder": "Search plugins, skills, and friends...",
        "all_label": "All",
        "showing_label": "Showing",
        "of_label": "of",
        "items_label": "items",
        "empty_label": "No items match the current filter.",
        "entry_point_label": "Entry point",
        "path_label": "Path",
        "install_command_label": "Install command",
        "create_command_label": "Create command",
        "copy_label": "Copy",
        "copied_label": "Copied",
        "readme_label": "README",
        "skill_doc_label": "SKILL.md",
        "category_labels": {
            "Plugins": "Plugins",
            "Templates": "Templates",
            "Skills": "Skills",
            "Friends": "Friends",
        },
        "badge_labels": {
            "plugin": "plugin",
            "template": "template",
            "skill": "skill",
            "bundled": "bundled",
            "local": "local",
            "friend": "friend",
        },
    },
    "zh": {
        "locale": "zh",
        "title": "目录",
        "summary": "这里收录了本仓库内部及周边生态中的插件、技能和相关项目。",
        "intro_kicker": "$ repo hub",
        "intro_body": '从这里快速跳到各个 README 或 <code>SKILL.md</code>。更完整的 Bub 生态目录请看 <a href="https://hub.bub.build">hub.bub.build</a>。',
        "search_placeholder": "搜索插件、技能和生态项目...",
        "all_label": "全部",
        "showing_label": "显示",
        "of_label": "/",
        "items_label": "项",
        "empty_label": "当前筛选条件下没有匹配项。",
        "entry_point_label": "入口点",
        "path_label": "路径",
        "install_command_label": "安装命令",
        "create_command_label": "创建命令",
        "copy_label": "复制",
        "copied_label": "已复制",
        "readme_label": "README",
        "skill_doc_label": "SKILL.md",
        "category_labels": {
            "Plugins": "插件",
            "Templates": "模板",
            "Skills": "技能",
            "Friends": "生态项目",
        },
        "badge_labels": {
            "plugin": "插件",
            "template": "模板",
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


_render_hub_page(Path(__file__).resolve().parent)


def on_config(config, **kwargs):
    docs_dir = Path(config["docs_dir"])
    _render_hub_page(docs_dir)
    return config
