import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import health, projects, chapters, characters, lore, timeline, settings, ai, jobs, export as export_router


def create_app() -> FastAPI:
    application = FastAPI(title="NovelForge Engine", version="0.1.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:9000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router, prefix="/api")
    application.include_router(projects.router, prefix="/api")
    application.include_router(chapters.router, prefix="/api")
    application.include_router(characters.router, prefix="/api")
    application.include_router(lore.router, prefix="/api")
    application.include_router(timeline.router, prefix="/api")
    application.include_router(settings.router, prefix="/api")
    application.include_router(ai.router, prefix="/api")
    application.include_router(jobs.router, prefix="/api")
    application.include_router(export_router.router, prefix="/api")

    return application


app = create_app()
