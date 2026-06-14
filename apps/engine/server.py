import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def get_app() -> "FastAPI":
    return create_app()


__all__ = ["get_app", "create_app"]
