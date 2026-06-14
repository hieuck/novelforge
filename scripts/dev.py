#!/usr/bin/env python3
"""Start both FastAPI engine and Vite frontend concurrently for development."""
import pathlib
import signal
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ENGINE_DIR = ROOT / "apps" / "engine"
DESKTOP_DIR = ROOT / "apps" / "desktop"


def find_python() -> str:
    for candidate in [
        ENGINE_DIR / ".venv" / "Scripts" / "python.exe",
        ENGINE_DIR / ".venv" / "bin" / "python3",
    ]:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def find_npm() -> str:
    return "npm.cmd" if sys.platform == "win32" else "npm"


procs: list = []


def cleanup(*_: object) -> None:
    print("\nStopping servers...")
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

python = find_python()
npm = find_npm()

print("=" * 55)
print("  NovelForge Dev Environment")
print("=" * 55)
print(f"  Engine   -> http://127.0.0.1:9000")
print(f"  Frontend -> http://127.0.0.1:5173")
print(f"  API docs -> http://127.0.0.1:9000/docs")
print("=" * 55)

procs.append(subprocess.Popen(
    [python, "-m", "uvicorn", "app:app",
     "--host", "127.0.0.1", "--port", "9000", "--reload"],
    cwd=str(ENGINE_DIR),
))

procs.append(subprocess.Popen(
    [npm, "run", "dev"],
    cwd=str(DESKTOP_DIR),
))

print("Both servers started. Press Ctrl+C to stop.\n")
try:
    for p in procs:
        p.wait()
except KeyboardInterrupt:
    cleanup()
