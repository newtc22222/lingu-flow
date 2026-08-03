import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CardSRSDataResponse(BaseModel):
    interval: int
    ease_factor: float = Field(alias="easeFactor")
    repetitions: int
    next_review_date: datetime = Field(alias="nextReviewDate")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class CardCreateRequest(BaseModel):
    front: str
    back: str
    deck_id: Optional[uuid.UUID] = Field(default=None, alias="deckId")

    model_config = ConfigDict(populate_by_name=True)


class CardUpdateRequest(BaseModel):
    front: str
    back: str
    deck_id: Optional[uuid.UUID] = Field(default=None, alias="deckId")

    model_config = ConfigDict(populate_by_name=True)


class CardReviewRequest(BaseModel):
    score: int = Field(ge=1, le=4)

    model_config = ConfigDict(populate_by_name=True)


class CardResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID = Field(alias="userId")
    deck_id: Optional[uuid.UUID] = Field(default=None, alias="deckId")
    front: str
    back: str
    srs_data: CardSRSDataResponse = Field(alias="srsData")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def assemble_srs_data(cls, data: Any) -> Any:
        """Construct srsData nested dict from SQLAlchemy Card model fields if needed."""
        if hasattr(data, "srs_interval"):
            srs = {
                "interval": getattr(data, "srs_interval", 0),
                "easeFactor": getattr(data, "srs_ease_factor", 2.5),
                "repetitions": getattr(data, "srs_repetitions", 0),
                "nextReviewDate": getattr(data, "srs_next_review", datetime.now()),
            }
            # Return dict for Pydantic parsing
            return {
                "id": getattr(data, "id"),
                "userId": getattr(data, "user_id"),
                "deckId": getattr(data, "deck_id", None),
                "front": getattr(data, "front"),
                "back": getattr(data, "back"),
                "srsData": srs,
                "createdAt": getattr(data, "created_at"),
                "updatedAt": getattr(data, "updated_at"),
            }
        return data
