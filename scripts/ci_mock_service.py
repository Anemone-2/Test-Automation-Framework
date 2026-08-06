"""Run the Flask Mock service as a CI-owned, fully detached process."""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = PROJECT_ROOT / "report" / "ci-runtime"
MOCK_SCRIPT = PROJECT_ROOT / "mock_server" / "api_server" / "base" / "flask_service.py"


def main() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["DATA_STORES_ENABLED"] = "true"
    os.chdir(PROJECT_ROOT)

    stdout = (RUNTIME_DIR / "mock-server.out.log").open("a", encoding="utf-8", buffering=1)
    stderr = (RUNTIME_DIR / "mock-server.err.log").open("a", encoding="utf-8", buffering=1)
    sys.stdout = stdout
    sys.stderr = stderr
    runpy.run_path(str(MOCK_SCRIPT), run_name="__main__")


if __name__ == "__main__":
    main()
