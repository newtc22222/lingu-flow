import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
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

        await db.commit()
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

    async def create_card(
        self, db: AsyncSession, user_id: uuid.UUID, req: CardCreateRequest
    ) -> Card:
        """Create a new flashcard for user."""
        card = Card(
            user_id=user_id,
            deck_id=req.deck_id,
            front=req.front,
            back=req.back,
        )
        db.add(card)
        await db.commit()
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

        card.front = req.front
        card.back = req.back
        card.deck_id = req.deck_id

        await db.commit()
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
        await db.commit()
        return True
