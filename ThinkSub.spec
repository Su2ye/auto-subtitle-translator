# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

PROJECT_ROOT = Path.cwd()

a = Analysis(
    ["src/main.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=[
        (str(PROJECT_ROOT / "ffmpeg/bin/ffmpeg.exe"), "ffmpeg/bin"),
        (str(PROJECT_ROOT / "ffmpeg/bin/ffprobe.exe"), "ffmpeg/bin"),
    ],
    datas=[
        (str(PROJECT_ROOT / "src/gui/resources"), "src/gui/resources"),
    ],
    hiddenimports=[
        "transformers",
        "sentencepiece",
        "ctranslate2",
        "onnxruntime",
        "soundfile",
        "numpy",
        "tokenizers",
        "huggingface_hub",
        "faster_whisper",
    ],
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
    name="ThinkSub",
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
    icon=str(PROJECT_ROOT / "src/gui/resources/icon.ico"),
)
