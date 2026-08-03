import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class DeckCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class DeckUpdateRequest(BaseModel):
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class DeckResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID = Field(alias="userId")
    name: str
    description: Optional[str] = None
    card_count: int = Field(default=0, alias="cardCount")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
