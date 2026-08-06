from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.database import AsyncSessionLocal, engine
from app.routers import (
    auth,
    cards,
    dashboard,
    decks,
    events,
    exams,
    health,
    media,
    questions,
)
from app.seed.exam_seed import seed_builtin_exams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("linguflow")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting LinguFlow FastAPI Backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Port: {settings.PORT}")

    # Run idempotent built-in exam seeding on startup
    try:
        async with AsyncSessionLocal() as session:
            await seed_builtin_exams(session)
    except Exception as e:
        logger.warning(f"⚠️ Built-in exam seed skipped (DB not ready or error): {e}")

    yield
    logger.info("🛑 Shutting down LinguFlow FastAPI Backend...")
    await engine.dispose()


app = FastAPI(
    title="LinguFlow API",
    description="FastAPI Backend for LinguFlow Language Certification Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(cards.router)
app.include_router(dashboard.router)
app.include_router(decks.router)
app.include_router(exams.router)
app.include_router(questions.router)
app.include_router(events.router)
app.include_router(media.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)
