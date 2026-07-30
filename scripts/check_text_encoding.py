"""Reject text file I/O that relies on the platform default encoding."""

from __future__ import annotations

import ast
import re
import sys
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = ("src", "tests", "scripts", "contrib", "templates", "skills")
TEXT_PATH_METHODS = {"read_text", "write_text"}
TEMPLATE_EXPRESSION = re.compile(r"\{\{[^{}\n]*\}\}")
BINARY_OPEN_BASELINE = "encoding-check: binary"


def _has_encoding_argument(call: ast.Call) -> bool:
    return any(keyword.arg == "encoding" for keyword in call.keywords)


def _mode_argument(call: ast.Call, position: int) -> str | None:
    for keyword in call.keywords:
        if keyword.arg == "mode" and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
            return keyword.value.value
    if (
        len(call.args) > position
        and isinstance(call.args[position], ast.Constant)
        and isinstance(call.args[position].value, str)
    ):
        return call.args[position].value
    return None


def _is_text_io_without_encoding(call: ast.Call) -> bool:
    if _has_encoding_argument(call):
        return False

    if isinstance(call.func, ast.Name) and call.func.id == "open":
        mode = _mode_argument(call, 1)
        return mode is None or "b" not in mode

    if not isinstance(call.func, ast.Attribute):
        return False
    if call.func.attr in TEXT_PATH_METHODS:
        return True
    if call.func.attr == "open":
        if isinstance(call.func.value, ast.Name) and call.func.value.id in {
            "os",
            "tarfile",
            "zipfile",
            "gzip",
            "_BoundedTarFile",
        }:
            return False
        mode = _mode_argument(call, 0)
        return mode is None or "b" not in mode
    return False


def _python_files() -> Iterable[Path]:
    for root_name in SOURCE_ROOTS:
        root = ROOT / root_name
        if root.is_dir():
            yield from sorted(root.rglob("*.py"))


def _source_for_parsing(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    if "templates" in path.relative_to(ROOT).parts:
        return TEMPLATE_EXPRESSION.sub("template_value", source)
    return source


def main() -> int:
    violations: list[str] = []
    for path in _python_files():
        source = _source_for_parsing(path)
        binary_baseline_lines = {
            line_number for line_number, line in enumerate(source.splitlines(), start=1) if BINARY_OPEN_BASELINE in line
        }
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and node.lineno not in binary_baseline_lines
                and _is_text_io_without_encoding(node)
            ):
                relative_path = path.relative_to(ROOT).as_posix()
                violations.append(f"{relative_path}:{node.lineno}: explicit encoding= is required for text file I/O")

    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
