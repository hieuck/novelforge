#!/usr/bin/env python3
"""Cross-platform self-updater for NovelForge, inspired by Hermes update flow."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

NOVELFORGE_ROOT = Path(__file__).resolve().parent.parent
REMOTE_URL = os.environ.get("NOVELFORGE_REMOTE", "https://github.com/hieuck/novelforge.git")
BRANCH = os.environ.get("NOVELFORGE_BRANCH", "main")
HISTORY_FILE = Path(os.environ.get("NOVELFORGE_HISTORY_PATH", NOVELFORGE_ROOT / "logs" / "update_history.log"))
LOCK_FILE = Path(os.environ.get("NOVELFORGE_LOCK_PATH", NOVELFORGE_ROOT / ".novelforge-update.lock"))


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=str(NOVELFORGE_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def read_last_history_commit() -> str | None:
    if HISTORY_FILE.exists():
        last = ""
        for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                last = line.strip()
        if "=>" in last:
            return last.split("=>")[-1].strip()
        return last.split()[-1]
    return None


def log_commit_note(commit: str):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    note = HISTORY_FILE.read_text(encoding="utf-8") if HISTORY_FILE.exists() else ""
    note = f"{note}{commit}\n" if note else f"{commit}\n"
    HISTORY_FILE.write_text(note, encoding="utf-8")


def acquire_lock():
    if LOCK_FILE.exists():
        raise RuntimeError(f"Update already in progress: {LOCK_FILE}")
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOCK_FILE.write_text("lock", encoding="utf-8")


def release_lock():
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


def branch() -> str:
    return BRANCH


def fetch() -> str | None:
    result = run(["git", "fetch", REMOTE_URL, branch()])
    if result.returncode == 0:
        return None
    return result.stderr.strip() or result.stdout.strip() or "git fetch failed"


def install_uv():
    try:
        shutil.which("uv")
    except Exception:
        shutil.which("uv")
    if shutil.which("uv") is None:
        raise RuntimeError("uv is not installed")


def install_deps_uv():
    install_uv()
    result = run(["uv", "sync", "--frozen", "--all-extras"])
    if result.returncode == 0:
        return None
    return result.stderr.strip() or result.stdout.strip() or "uv sync failed"


def install_deps_pip(fallback: bool):
    args = ["pip", "install", "--upgrade", ".[all]"]
    if fallback:
        args = ["pip", "install", "--upgrade", "."]
    result = run(args)
    if result.returncode == 0:
        return None
    return result.stderr.strip() or result.stdout.strip() or "pip install failed"


def restore_last_install_stash():
    result = run(["git", "stash", "pop"])
    if result.returncode == 0:
        return None
    return result.stderr.strip() or result.stdout.strip() or "git stash pop failed"


def main() -> int:
    try:
        final_commit = None
        last_commit = read_last_history_commit()
        print(f"Last known commit: {last_commit or 'unknown'}")
        acquire_lock()
        try:
            fetch_err = fetch()
            if fetch_err and "Node" not in fetch_err:
                raise RuntimeError(fetch_err)
            result = run(["git", "rev-parse", f"origin/{branch()}"])
            if result.returncode == 0:
                final_commit = result.stdout.strip()
                if final_commit == last_commit:
                    print("Already up to date")
                    return 0
            else:
                final_commit = "unknown"
            print(f"Updating to {final_commit} ...")
            if last_commit:
                run(["git", "show", "-s", "--stat", "--oneline", last_commit])
            run(
                [
                    "git",
                    "log",
                    f"{last_commit or 'HEAD'}..origin/{branch()}",
                    "--oneline",
                    "--decorate",
                    "--max-count=5",
                ]
            )
            if last_commit:
                run(["git", "diff", "--stat", f"{last_commit}..origin/{branch()}"])

            print("Stashing local changes...")
            run(["git", "stash", "--include-untracked", "-m", "autoupdate stash"])

            pull_err = None
            update_error = False
            try:
                pull = run(["git", "pull", "--ff-only", REMOTE_URL, branch()])
                if pull.returncode != 0:
                    pull_err = pull.stderr.strip() or pull.stdout.strip() or "git pull failed"
                    print(f"git pull failed => preparing fallback reset: {pull_err}")
                    update_error = True
                else:
                    result = run(["git", "rev-parse", "HEAD"])
                    if result.returncode == 0:
                        final_commit = result.stdout.strip()
                    else:
                        update_error = True
            finally:
                run(["git", "config", "user.name", "NovelForge Updater"])
                run(["git", "config", "user.email", "updater@novelforge.app"])
                if update_error:
                    print("git save")
                    run(["git", "reset", "--hard", f"origin/{branch()}"])
                    result = run(["git", "rev-parse", "HEAD"])
                    if result.returncode == 0:
                        final_commit = result.stdout.strip()
                    else:
                        print("[ERROR] fallback reset failed")
                        print("Attempting to restore stashed changes...")
                        restore = restore_last_install_stash()
                        if restore:
                            print(f"[WARN] stash restore failed: {restore}")
                        sys.exit(1)

            print(f"Installing dependencies for {final_commit} ...")

            install_err = install_deps_uv()
            if install_err:
                print(f"[WARN] uv install failed: {install_err}")
                install_err = install_deps_pip(fallback=True)
                if install_err:
                    print(f"[ERROR] pip install failed: {install_err}")

            if install_err:
                print("Attempting to restore stashed changes...")
                restore = restore_last_install_stash()
                if restore:
                    print(f"[WARN] stash restore failed: {restore}")
                raise RuntimeError(install_err)

            log_commit_note(final_commit)
            print("Update complete. Restart the app to apply changes.")
            return 0
        finally:
            release_lock()
    except Exception as exc:
        print(f"[ERROR] Update failed: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
