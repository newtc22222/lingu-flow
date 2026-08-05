from typing import List
from pydantic import BaseModel, ConfigDict, Field


class LevelProgressResponse(BaseModel):
    id: str
    index: int
    status: str  # "done" | "current" | "locked"

    model_config = ConfigDict(populate_by_name=True)


class WorldProgressResponse(BaseModel):
    id: str
    title: str
    levels: List[LevelProgressResponse]
    progress_percent: int = Field(alias="progressPercent")
    sub_label: str = Field(alias="subLabel")

    model_config = ConfigDict(populate_by_name=True)


class DashboardProgressResponse(BaseModel):
    total_xp: int = Field(alias="totalXp")
    streak_days: int = Field(alias="streakDays")
    exam_readiness: int = Field(alias="examReadiness")
    worlds: List[WorldProgressResponse]

    model_config = ConfigDict(populate_by_name=True)
