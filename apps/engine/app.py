from __future__ import annotations

import logging

import db.base
from _version import VERSION
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routes.agent import router as agent_router
from routes.ai import router as ai_router
from routes.backup import router as backup_router
from routes.chapters import router as chapters_router
from routes.stats import router as stats_router
from routes.characters import router as characters_router
from routes.export import router as export_router
from routes.generate import router as generate_router
from routes.health import router as health_router
from routes.imports import router as imports_router
from routes.jobs import router as jobs_router
from routes.lore import router as lore_router
from routes.projects import router as projects_router
from routes.search import router as search_router
from routes.settings import router as settings_router
from routes.timeline import router as timeline_router
from routes.update import router as update_router
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
    logger = logging.getLogger("novelforge.engine")

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

    import time as _time

    @application.middleware("http")
    async def request_logging(request: Request, call_next):
        start = _time.perf_counter()
        response = await call_next(request)
        elapsed = _time.perf_counter() - start
        if elapsed > 0.5:
            logger.warning("SLOW %s %s (%.2fs)", request.method, request.url.path, elapsed)
        else:
            logger.info("%s %s (%.2fs)", request.method, request.url.path, elapsed)
        return response

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
        backup_router,
        stats_router,
    ]:
        application.include_router(rtr, prefix="/api")

    @application.on_event("shutdown")
    async def shutdown():
        logger.info("Shutting down NovelForge Engine — closing DB connections")
        db.base.engine.dispose()

    return application


app = create_app()
