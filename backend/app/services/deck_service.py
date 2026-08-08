import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.deck import Deck
from app.schemas.deck import DeckCreateRequest, DeckUpdateRequest


class DeckService:
    async def get_all_decks(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """Fetch all decks owned by user with dynamic card_count aggregated."""
        # Left join Deck and Card to count total cards per deck
        stmt = (
            select(Deck, func.count(Card.id).label("card_count"))
            .outerjoin(Card, Card.deck_id == Deck.id)
            .where(Deck.user_id == user_id)
            .group_by(Deck.id)
            .order_by(Deck.created_at.desc())
        )
        result = await db.execute(stmt)
        rows = result.all()

        decks_data = []
        for deck, card_count in rows:
            decks_data.append({
                "id": deck.id,
                "userId": deck.user_id,
                "name": deck.name,
                "description": deck.description,
                "cardCount": card_count,
                "createdAt": deck.created_at,
                "updatedAt": deck.updated_at,
            })
        return decks_data

    async def create_deck(
        self, db: AsyncSession, user_id: uuid.UUID, req: DeckCreateRequest
    ) -> Dict[str, Any]:
        """Create a new deck for user."""
        deck = Deck(
            user_id=user_id,
            name=req.name,
            description=req.description,
        )
        db.add(deck)
        await db.flush()
        await db.refresh(deck)

        return {
            "id": deck.id,
            "userId": deck.user_id,
            "name": deck.name,
            "description": deck.description,
            "cardCount": 0,
            "createdAt": deck.created_at,
            "updatedAt": deck.updated_at,
        }

    async def update_deck(
        self,
        db: AsyncSession,
        deck_id: uuid.UUID,
        user_id: uuid.UUID,
        req: DeckUpdateRequest,
    ) -> Optional[Dict[str, Any]]:
        """Update an existing deck name and description."""
        result = await db.execute(
            select(Deck).where(Deck.id == deck_id, Deck.user_id == user_id)
        )
        deck = result.scalar_one_or_none()
        if not deck:
            return None

        deck.name = req.name
        deck.description = req.description

        await db.flush()
        await db.refresh(deck)

        # Get card_count
        count_stmt = select(func.count(Card.id)).where(Card.deck_id == deck.id)
        card_count = (await db.execute(count_stmt)).scalar() or 0

        return {
            "id": deck.id,
            "userId": deck.user_id,
            "name": deck.name,
            "description": deck.description,
            "cardCount": card_count,
            "createdAt": deck.created_at,
            "updatedAt": deck.updated_at,
        }

    async def delete_deck(
        self, db: AsyncSession, deck_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Delete a deck."""
        result = await db.execute(
            select(Deck).where(Deck.id == deck_id, Deck.user_id == user_id)
        )
        deck = result.scalar_one_or_none()
        if not deck:
            return False

        await db.delete(deck)
        await db.flush()
        return True
