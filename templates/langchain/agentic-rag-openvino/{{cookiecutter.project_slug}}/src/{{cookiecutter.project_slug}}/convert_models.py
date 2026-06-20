"""Download and convert 3 models to OpenVINO IR format.

Usage:
    uv run convert-models
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


MODELS = {
    "llm": {
        "model_id": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "output_dir": "./models/tiny-llama-1b-chat/INT4_compressed_weights",
        "task": "text-generation-with-past",
        "weight_format": "int4",
    },
    "embedding": {
        "model_id": "BAAI/bge-small-en-v1.5",
        "output_dir": "./models/bge-small-en-v1.5",
        "task": "feature-extraction",
        "weight_format": None,
    },
    "reranker": {
        "model_id": "BAAI/bge-reranker-v2-m3",
        "output_dir": "./models/bge-reranker-v2-m3",
        "task": "text-classification",
        "weight_format": None,
    },
}


def convert_model(name: str, cfg: dict) -> None:
    output = Path(cfg["output_dir"])
    if (output / "openvino_model.xml").exists():
        print(f"[{name}] Already converted at {output}, skipping.")
        return

    cmd = [
        sys.executable, "-m", "optimum.exporters.openvino",
        "--model", cfg["model_id"],
        "--task", cfg["task"],
    ]
    if cfg.get("weight_format"):
        cmd += ["--weight-format", cfg["weight_format"]]
    cmd.append(str(output))

    print(f"[{name}] Converting {cfg['model_id']} -> {output}")
    print(f"  Command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"[{name}] Done.")


def main() -> None:
    for name, cfg in MODELS.items():
        convert_model(name, cfg)
    print("\nAll models converted. You can now run `uv run ingest` and `uv run langgraph dev`.")


if __name__ == "__main__":
    main()
