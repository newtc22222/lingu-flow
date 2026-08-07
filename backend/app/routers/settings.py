from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.settings import UserSettingsPayload, UserSettingsResponse
from app.services import settings_service

router = APIRouter(prefix="/api/settings", tags=["Settings"])


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await settings_service.get_user_settings(db, current_user)


@router.put("", response_model=UserSettingsResponse)
async def save_settings(
    payload: UserSettingsPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await settings_service.update_user_settings(db, current_user, payload)
