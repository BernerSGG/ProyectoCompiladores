"""Root launcher for the RadarScriptCompiler pipeline."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> None:
    """Execute the compiler entry point located in src/main.py."""
    project_root = Path(__file__).resolve().parent
    src_root = project_root / "src"
    entrypoint = src_root / "main.py"
    if str(src_root) not in sys.path:
        sys.path.insert(0, str(src_root))
    runpy.run_path(str(entrypoint), run_name="__main__")


if __name__ == "__main__":
    main()
