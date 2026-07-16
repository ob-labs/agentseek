from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .media import extract_archive_safely
from .sample_pack import sample_pack_dir
from .settings import get_settings
from .store import HybridImageStore


def _resolve_source(source: Path) -> Path:
    settings = get_settings()
    if source.is_dir():
        return source
    if source.is_file():
        target = settings.media_data_dir / "extracted" / source.stem
        return extract_archive_safely(source, target)
    raise FileNotFoundError(f"Source not found: {source}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest images into the hybrid RAG image store.")
    parser.add_argument(
        "source",
        nargs="?",
        default=str(sample_pack_dir() / "images"),
        help="Image directory or supported archive. Defaults to the built-in sample pack.",
    )
    args = parser.parse_args()

    source = _resolve_source(Path(args.source))
    records = HybridImageStore().ingest_directory(source)
    if not records:
        print(f"No supported images found in {source}.")
        sys.exit(1)
    print(f"Indexed {len(records)} image(s) from {source}.")


if __name__ == "__main__":
    main()
