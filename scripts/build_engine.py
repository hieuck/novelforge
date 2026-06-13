#!/usr/bin/env python3
"""
Build the Python engine into a standalone executable using PyInstaller.

Usage:
    python scripts/build_engine.py

Output: apps/engine/dist/engine/engine[.exe]

electron-builder extraResources picks up apps/engine/dist/engine/
and bundles it as resources/engine/ inside the installed app.
"""
import subprocess
import sys
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT / "apps" / "engine"
DIST_DIR = ENGINE_DIR / "dist"
BUILD_DIR = ENGINE_DIR / "build_pyinstaller"


def find_python() -> str:
    for candidate in [
        ENGINE_DIR / ".venv" / "Scripts" / "python.exe",
        ENGINE_DIR / ".venv" / "bin" / "python3",
    ]:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def main() -> None:
    python = find_python()
    print(f"Python: {python}")

    subprocess.check_call([python, "-m", "pip", "install", "pyinstaller>=6.0", "-q"])

    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d)

    cmd = [
        python, "-m", "PyInstaller",
        "run.py",
        "--name", "engine",
        "--onedir",
        "--noconfirm", "--clean",
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--specpath", str(BUILD_DIR),
        "--collect-all", "sqlalchemy",
        "--hidden-import", "uvicorn.logging",
        "--hidden-import", "uvicorn.loops.auto",
        "--hidden-import", "uvicorn.protocols.http.auto",
        "--hidden-import", "uvicorn.protocols.websockets.auto",
        "--hidden-import", "uvicorn.lifespan.on",
        "--hidden-import", "anyio._backends._asyncio",
        "--hidden-import", "anyio._backends._trio",
        "--hidden-import", "httptools",
        "--hidden-import", "websockets",
        "--hidden-import", "aiosqlite",
        "--hidden-import", "email_validator",
    ]

    print("Running PyInstaller...")
    subprocess.check_call(cmd, cwd=str(ENGINE_DIR))

    exe = DIST_DIR / "engine" / ("engine.exe" if sys.platform == "win32" else "engine")
    if exe.exists():
        print(f"Built: {exe}  ({exe.stat().st_size / 1_048_576:.1f} MB)")
    else:
        print(f"Build done — check {DIST_DIR / 'engine'}")


if __name__ == "__main__":
    main()
