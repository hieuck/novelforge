from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

from _version import VERSION
import db.base
from services.search import init_fts


def create_app() -> FastAPI:
    # Create all SQLAlchemy tables
    db.base.Base.metadata.create_all(bind=db.base.engine)

    # Initialise FTS5 virtual tables (idempotent)
    init_fts()

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
    ]:
        application.include_router(rtr, prefix="/api")

    return application


app = create_app()
