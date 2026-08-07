from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class UserSettingsPayload(BaseModel):
    """
    The JSON body that the frontend sends when saving settings.
    All fields are optional — only changed fields need to be sent.
    """
    locale: Optional[str] = Field(default=None, description="'vi' or 'en'")
    crt_enabled: Optional[bool] = Field(default=None, alias="crtEnabled")
    daily_xp_goal: Optional[int] = Field(default=None, alias="dailyXpGoal")
    audio_sfx_enabled: Optional[bool] = Field(default=None, alias="audioSfxEnabled")
    notifications_enabled: Optional[bool] = Field(default=None, alias="notificationsEnabled")

    model_config = ConfigDict(populate_by_name=True)


class UserSettingsResponse(BaseModel):
    """
    The response shape returned by the GET /api/settings endpoint.
    """
    locale: str = "vi"
    crt_enabled: bool = Field(default=True, alias="crtEnabled")
    daily_xp_goal: int = Field(default=50, alias="dailyXpGoal")
    audio_sfx_enabled: bool = Field(default=False, alias="audioSfxEnabled")
    notifications_enabled: bool = Field(default=False, alias="notificationsEnabled")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
