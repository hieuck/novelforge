from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI

from app import create_app


def get_app() -> FastAPI:
    return create_app()


__all__ = ["get_app", "create_app"]
