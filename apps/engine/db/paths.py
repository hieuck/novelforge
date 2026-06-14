from __future__ import annotations

import os
import sys
from pathlib import Path


def get_data_dir() -> Path:
    env = os.environ.get("NOVELFORGE_DATA_DIR")
    if env:
        p = Path(env).resolve()
    elif sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        p = Path(base) / "novelforge" / "data"
    elif sys.platform == "darwin":
        p = Path.home() / "Library" / "Application Support" / "novelforge" / "data"
    else:
        p = Path.home() / ".local" / "share" / "novelforge" / "data"
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_db_url() -> str:
    data_dir = get_data_dir()
    db_path = data_dir / "novelforge.db"
    return f"sqlite:///{db_path.as_posix()}"
