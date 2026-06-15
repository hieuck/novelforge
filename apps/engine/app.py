from __future__ import annotations
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from routes.health import router as health_router
from routes.projects import router as projects_router
from routes.chapters import router as chapters_router
from routes.characters import router as characters_router
from routes.lore import router as lore_router
from routes.timeline import router as timeline_router
from routes.settings import router as settings_router
from routes.ai import router as ai_router
from routes.jobs import router as jobs_router
from routes.export import router as export_router
from routes.imports import router as imports_router
from routes.search import router as search_router
from routes.agent import router as agent_router
from routes.update import router as update_router
from routes.generate import router as generate_router

from _version import VERSION
import db.base
from services.search import init_fts


def create_app() -> FastAPI:
    # Create all SQLAlchemy tables (safe — only creates missing tables)
    db.base.Base.metadata.create_all(bind=db.base.engine)

    # Schema migration: add columns added after initial release
    from scripts.migrate import run as run_migration
    run_migration()

    # Initialise FTS5 virtual tables (idempotent)
    init_fts()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    application = FastAPI(
        title="NovelForge Engine",
        version=VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logging.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # Register all routers under /api prefix
    for rtr in [
        health_router,
        projects_router,
        chapters_router,
        characters_router,
        lore_router,
        timeline_router,
        settings_router,
        ai_router,
        jobs_router,
        export_router,
        imports_router,
        search_router,
        agent_router,
        update_router,
        generate_router,
    ]:
        application.include_router(rtr, prefix="/api")

    return application


app = create_app()
