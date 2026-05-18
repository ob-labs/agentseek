from __future__ import annotations

from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader


def _render_hub_page(docs_dir: Path) -> None:
    data_path = docs_dir / "_data" / "hub.yml"
    template_dir = docs_dir / "_templates"
    output_path = docs_dir / "hub.md"

    data = yaml.safe_load(data_path.read_text(encoding="utf-8")) or {}
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("hub.md.j2")
    rendered = template.render(categories=data.get("categories", []))
    output_path.write_text(rendered.rstrip() + "\n", encoding="utf-8")


def on_config(config, **kwargs):
    docs_dir = Path(config["docs_dir"])
    _render_hub_page(docs_dir)
    return config
