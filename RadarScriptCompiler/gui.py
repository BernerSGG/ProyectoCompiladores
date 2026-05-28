"""Root launcher for the RadarScriptCompiler Tkinter interface."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


BASE_DIR = Path(getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))))
SRC_DIR = BASE_DIR / "src"

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def _load_gui_module():
    """Load the src/gui.py module without relying on runpy."""
    module_path = SRC_DIR / "gui.py"
    if not module_path.exists():
        raise FileNotFoundError(f"No se encontro el modulo de interfaz: {module_path}")

    spec = importlib.util.spec_from_file_location("radarscript_gui", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo cargar el modulo principal desde: {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    """Execute the GUI entry point located in src/gui.py."""
    gui_module = _load_gui_module()
    gui_module.main()


if __name__ == "__main__":
    main()
