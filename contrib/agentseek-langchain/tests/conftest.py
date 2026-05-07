from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
LANGCHAIN_SRC = REPO_ROOT / "contrib" / "agentseek-langchain" / "src"
LANGCHAIN_EXAMPLES = REPO_ROOT / "contrib" / "agentseek-langchain" / "examples"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if str(LANGCHAIN_SRC) not in sys.path:
    sys.path.insert(0, str(LANGCHAIN_SRC))

if str(LANGCHAIN_EXAMPLES) not in sys.path:
    sys.path.insert(0, str(LANGCHAIN_EXAMPLES))
