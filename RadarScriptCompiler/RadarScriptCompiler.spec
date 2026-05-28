# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


PROJECT_ROOT = Path(r"C:\Users\garci\Downloads\proyecto\RadarScriptCompiler")
SRC_ROOT = PROJECT_ROOT / "src"
ICON_PATH = PROJECT_ROOT / "assets" / "RadarScriptCompiler.ico"
VERSION_PATH = PROJECT_ROOT / "assets" / "version_info.txt"

datas = [
    (str(SRC_ROOT), "src"),
    (str(PROJECT_ROOT / "tests"), "tests"),
    (str(PROJECT_ROOT / "outputs"), "outputs"),
    (str(PROJECT_ROOT / "README.md"), "."),
    (str(PROJECT_ROOT / "MANUAL_USUARIO.md"), "."),
    (str(PROJECT_ROOT / "MANUAL_TECNICO.md"), "."),
    (str(PROJECT_ROOT / "ESPECIFICACION_LENGUAJE.md"), "."),
    (str(ICON_PATH), "assets"),
]
datas += collect_data_files("customtkinter")

hiddenimports = [
    "diagnostics",
    "codegen.codegen",
    "intermediate.intermediate",
    "lexer.lexer",
    "parser.parser",
    "semantic.semantic",
    "vm.vm",
    "src",
    "src.gui",
    "src.diagnostics",
    "src.codegen.codegen",
    "src.intermediate.intermediate",
    "src.lexer.lexer",
    "src.parser.parser",
    "src.semantic.semantic",
    "src.vm.vm",
    "customtkinter",
    "darkdetect",
    "tkinter",
    "tkinter.filedialog",
    "tkinter.ttk",
    "tkinter.font",
    "tkinter.scrolledtext",
]
hiddenimports += collect_submodules("customtkinter")

a = Analysis(
    ["gui.py"],
    pathex=[str(PROJECT_ROOT), str(SRC_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="RadarScriptCompiler",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_PATH),
    version=str(VERSION_PATH),
)
