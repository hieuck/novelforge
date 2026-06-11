from fastapi import FastAPI, APIRouter
from routes import projects, chapters, characters, lore, timeline, settings, jobs, ai, export, health

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(chapters.router, prefix="/chapters", tags=["chapters"])
router.include_router(characters.router, prefix="/characters", tags=["characters"])
router.include_router(lore.router, prefix="/lore", tags=["lore"])
router.include_router(timeline.router, prefix="/timeline", tags=["timeline"])
router.include_router(settings.router, prefix="/settings", tags=["settings"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(ai.router, prefix="/ai", tags=["ai"])
router.include_router(export.router, prefix="/export", tags=["export"])

app = FastAPI()
app.include_router(router)
