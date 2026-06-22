"""Download and convert models to OpenVINO IR format.

Usage:
    uv run convert-models
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# Model IDs default to cookiecutter values but can be overridden via env vars.
LLM_MODEL_ID = os.getenv("LLM_MODEL_ID", "{{ cookiecutter.llm_model_id }}")
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "{{ cookiecutter.embedding_model_id }}")

MODELS = {
    "llm": {
        "model_id": LLM_MODEL_ID,
        "output_dir": "{{ cookiecutter.llm_model_path }}",
        "task": "text-generation-with-past",
        "weight_format": "int4",
    },
    "embedding": {
        "model_id": EMBEDDING_MODEL_ID,
        "output_dir": "{{ cookiecutter.embedding_model_path }}",
        "task": "feature-extraction",
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
