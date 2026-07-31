from fastapi import APIRouter
from app.config import get_settings

router = APIRouter(prefix="/api", tags=["Health"])
settings = get_settings()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": "LinguFlow Python API",
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }
