import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.card import (
    CardCreateRequest,
    CardResponse,
    CardReviewRequest,
    CardUpdateRequest,
)
from app.services.card_service import CardService

router = APIRouter(prefix="/api/cards", tags=["Cards"])
card_service = CardService()


@router.get("/study", response_model=List[CardResponse])
async def get_cards_to_study(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch all active cards due for review (srs_next_review <= current time)."""
    cards = await card_service.get_cards_to_study(db, current_user.id)
    return [CardResponse.model_validate(c) for c in cards]


@router.post("/review/{card_id}", response_model=CardResponse)
async def review_card(
    card_id: uuid.UUID,
    req: CardReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Process a review score (1-4) for a card using the SM-2 algorithm."""
    card = await card_service.process_review(
        db, card_id=card_id, user_id=current_user.id, score=req.score
    )
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found or not authorized",
        )
    return CardResponse.model_validate(card)


@router.get("", response_model=List[CardResponse])
async def get_all_cards(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch all flashcards owned by current user."""
    cards = await card_service.get_all_cards(db, current_user.id)
    return [CardResponse.model_validate(c) for c in cards]


@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    req: CardCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new flashcard."""
    card = await card_service.create_card(db, current_user.id, req)
    return CardResponse.model_validate(card)


@router.put("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: uuid.UUID,
    req: CardUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing flashcard."""
    card = await card_service.update_card(db, card_id, current_user.id, req)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found or not authorized",
        )
    return CardResponse.model_validate(card)


@router.delete("/{card_id}")
async def delete_card(
    card_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a flashcard."""
    success = await card_service.delete_card(db, card_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found or not authorized",
        )
    return {"success": True}
