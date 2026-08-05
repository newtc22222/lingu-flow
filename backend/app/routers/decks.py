import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.card import CardReorderRequest, CardResponse
from app.schemas.deck import DeckCreateRequest, DeckResponse, DeckUpdateRequest
from app.services.card_service import CardService
from app.services.deck_service import DeckService

router = APIRouter(prefix="/api/decks", tags=["Decks"])
deck_service = DeckService()
card_service = CardService()


@router.get("", response_model=List[DeckResponse])
async def get_all_decks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch all decks owned by current user with cardCount aggregated."""
    decks_data = await deck_service.get_all_decks(db, current_user.id)
    return [DeckResponse.model_validate(d) for d in decks_data]


@router.post("", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(
    req: DeckCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new deck."""
    deck_data = await deck_service.create_deck(db, current_user.id, req)
    return DeckResponse.model_validate(deck_data)


@router.put("/{deck_id}", response_model=DeckResponse)
async def update_deck(
    deck_id: uuid.UUID,
    req: DeckUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing deck."""
    deck_data = await deck_service.update_deck(db, deck_id, current_user.id, req)
    if not deck_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found or not authorized",
        )
    return DeckResponse.model_validate(deck_data)


@router.get("/{deck_id}/cards", response_model=List[CardResponse])
async def get_deck_cards(
    deck_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a deck's cards in display order — powers the deck detail view."""
    cards = await card_service.get_deck_cards(db, deck_id, current_user.id)
    return [CardResponse.model_validate(c) for c in cards]


@router.patch("/{deck_id}/cards/reorder", response_model=List[CardResponse])
async def reorder_deck_cards(
    deck_id: uuid.UUID,
    req: CardReorderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Persist a drag-and-drop reorder. `cardIds` must cover the deck exactly."""
    cards = await card_service.reorder_deck_cards(
        db, deck_id, current_user.id, req.card_ids
    )
    if cards is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="cardIds must contain exactly the cards in this deck",
        )
    return [CardResponse.model_validate(c) for c in cards]


@router.delete("/{deck_id}")
async def delete_deck(
    deck_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a deck."""
    success = await deck_service.delete_deck(db, deck_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found or not authorized",
        )
    return {"success": True}
