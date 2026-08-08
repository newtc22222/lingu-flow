import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.schemas.card import CardCreateRequest, CardUpdateRequest
from app.services.sm2_service import calculate_sm2


class CardService:
    async def get_cards_to_study(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> List[Card]:
        """Fetch all active cards for a user where srs_next_review <= current time."""
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(Card)
            .where(Card.user_id == user_id, Card.srs_next_review <= now)
            .order_by(Card.srs_next_review.asc())
        )
        return list(result.scalars().all())

    async def process_review(
        self, db: AsyncSession, card_id: uuid.UUID, user_id: uuid.UUID, score: int
    ) -> Optional[Card]:
        """Process a review score (1-4) for a card and update its SM-2 SRS data."""
        result = await db.execute(
            select(Card).where(Card.id == card_id, Card.user_id == user_id)
        )
        card = result.scalar_one_or_none()
        if not card:
            return None

        sm2_data = calculate_sm2(
            interval=card.srs_interval,
            ease_factor=card.srs_ease_factor,
            repetitions=card.srs_repetitions,
            score=score,
        )

        card.srs_interval = sm2_data["interval"]
        card.srs_ease_factor = sm2_data["ease_factor"]
        card.srs_repetitions = sm2_data["repetitions"]
        card.srs_next_review = sm2_data["next_review_date"]

        await db.flush()
        await db.refresh(card)
        return card

    async def get_all_cards(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> List[Card]:
        """Fetch all cards for a user sorted by created_at descending."""
        result = await db.execute(
            select(Card).where(Card.user_id == user_id).order_by(Card.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_deck_cards(
        self, db: AsyncSession, deck_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Card]:
        """Fetch a deck's cards in display order (position, then creation time)."""
        result = await db.execute(
            select(Card)
            .where(Card.deck_id == deck_id, Card.user_id == user_id)
            .order_by(Card.position.asc(), Card.created_at.asc())
        )
        return list(result.scalars().all())

    async def reorder_deck_cards(
        self,
        db: AsyncSession,
        deck_id: uuid.UUID,
        user_id: uuid.UUID,
        card_ids: List[uuid.UUID],
    ) -> Optional[List[Card]]:
        """
        Rewrite `position` for a deck's cards to match `card_ids`.

        Returns None when the id list doesn't exactly cover the deck's cards —
        a partial reorder would silently strand the omitted cards at whatever
        stale positions they already had, so it's rejected rather than applied.
        """
        cards = await self.get_deck_cards(db, deck_id, user_id)
        if not cards:
            return None

        by_id = {card.id: card for card in cards}
        if set(card_ids) != set(by_id) or len(card_ids) != len(cards):
            return None

        for index, card_id in enumerate(card_ids):
            by_id[card_id].position = index

        await db.flush()
        return await self.get_deck_cards(db, deck_id, user_id)

    async def _next_position(
        self, db: AsyncSession, deck_id: Optional[uuid.UUID], user_id: uuid.UUID
    ) -> int:
        """Append position for a new card — max(position) + 1 within its deck."""
        if deck_id is None:
            return 0
        result = await db.execute(
            select(func.max(Card.position)).where(
                Card.deck_id == deck_id, Card.user_id == user_id
            )
        )
        current_max = result.scalar()
        return 0 if current_max is None else current_max + 1

    async def create_card(
        self, db: AsyncSession, user_id: uuid.UUID, req: CardCreateRequest
    ) -> Card:
        """Create a new flashcard for user, appended to the end of its deck."""
        card = Card(
            user_id=user_id,
            deck_id=req.deck_id,
            front=req.front,
            back=req.back,
            image_url=req.image_url,
            notes=req.notes,
            position=await self._next_position(db, req.deck_id, user_id),
        )
        db.add(card)
        await db.flush()
        await db.refresh(card)
        return card

    async def update_card(
        self,
        db: AsyncSession,
        card_id: uuid.UUID,
        user_id: uuid.UUID,
        req: CardUpdateRequest,
    ) -> Optional[Card]:
        """Update an existing flashcard."""
        result = await db.execute(
            select(Card).where(Card.id == card_id, Card.user_id == user_id)
        )
        card = result.scalar_one_or_none()
        if not card:
            return None

        moved_deck = card.deck_id != req.deck_id

        card.front = req.front
        card.back = req.back
        card.deck_id = req.deck_id
        card.image_url = req.image_url
        card.notes = req.notes
        # Moving decks invalidates the old position — append to the new deck.
        if moved_deck:
            card.position = await self._next_position(db, req.deck_id, user_id)

        await db.flush()
        await db.refresh(card)
        return card

    async def delete_card(
        self, db: AsyncSession, card_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Delete a flashcard."""
        result = await db.execute(
            select(Card).where(Card.id == card_id, Card.user_id == user_id)
        )
        card = result.scalar_one_or_none()
        if not card:
            return False

        await db.delete(card)
        await db.flush()
        return True
