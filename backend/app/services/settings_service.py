from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.settings import UserSettings
from app.models.user import User
from app.schemas.settings import UserSettingsPayload, UserSettingsResponse

# Default values when no row exists yet.
DEFAULTS = {
    "locale": "vi",
    "crtEnabled": True,
    "dailyXpGoal": 50,
    "audioSfxEnabled": False,
    "notificationsEnabled": False,
}


async def get_user_settings(db: AsyncSession, user: User) -> UserSettingsResponse:
    """Return the persisted settings or defaults if no row exists."""
    row = await db.scalar(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )
    if row is None:
        return UserSettingsResponse(**DEFAULTS)

    merged = {**DEFAULTS, **row.settings}
    return UserSettingsResponse(**merged)


async def update_user_settings(
    db: AsyncSession, user: User, payload: UserSettingsPayload
) -> UserSettingsResponse:
    """Upsert user settings.  Only non-None fields from the payload are written."""
    row = await db.scalar(
        select(UserSettings).where(UserSettings.user_id == user.id)
    )

    # Build a dict of only the fields the client actually sent.
    updates = payload.model_dump(by_alias=True, exclude_none=True)

    if row is None:
        merged = {**DEFAULTS, **updates}
        row = UserSettings(user_id=user.id, settings=merged)
        db.add(row)
    else:
        merged = {**DEFAULTS, **row.settings, **updates}
        row.settings = merged

    await db.flush()
    return UserSettingsResponse(**merged)
