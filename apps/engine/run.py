import os
import sys

from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
except Exception as exc:  # pragma: no cover - used as bootstrap guard only
    raise ImportError("novelforge engine bootstrap failed: %s" % exc)

app = create_app()
application = app
