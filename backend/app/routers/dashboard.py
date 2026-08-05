from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardProgressResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
dashboard_service = DashboardService()


@router.get("/progress", response_model=DashboardProgressResponse)
async def get_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Progress HUD for the dashboard: XP, streak, exam readiness, and worlds."""
    progress = await dashboard_service.get_progress(db, current_user.id)
    return DashboardProgressResponse.model_validate(progress)
