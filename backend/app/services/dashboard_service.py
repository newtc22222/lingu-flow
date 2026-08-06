import uuid
from datetime import date, timedelta
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.card import Card
from app.models.deck import Deck
from app.models.session import ExamSession

# Cards per level node on a world's stage-select path.
LEVEL_SIZE = 5
# XP awarded per completed SM-2 repetition and per finished exam session.
XP_PER_REPETITION = 10
XP_PER_EXAM = 50
# Exam readiness averages only the most recent sessions, so an old bad run
# stops dragging the number down forever.
READINESS_WINDOW = 5


class DashboardService:
    """
    Derives the dashboard's progress HUD from data the app already stores.

    This is deliberately a cheap projection over Deck/Card/ExamSession rows,
    not an analytics pipeline — there is no events table to aggregate, and the
    real analytics work is tracked separately (issue #13).
    """

    async def get_progress(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        cards = list(
            (
                await db.execute(select(Card).where(Card.user_id == user_id))
            ).scalars().all()
        )
        decks = list(
            (
                await db.execute(
                    select(Deck)
                    .where(Deck.user_id == user_id)
                    .order_by(Deck.created_at.asc())
                )
            ).scalars().all()
        )
        sessions = list(
            (
                await db.execute(
                    select(ExamSession).where(
                        ExamSession.user_id == user_id,
                        ExamSession.status == "completed",
                    )
                )
            ).scalars().all()
        )

        return {
            "totalXp": self._total_xp(cards, sessions),
            "streakDays": self._streak_days(cards),
            "examReadiness": self._exam_readiness(sessions),
            "worlds": self._worlds(decks, cards),
        }

    def _total_xp(self, cards: List[Card], sessions: List[ExamSession]) -> int:
        review_xp = sum(c.srs_repetitions for c in cards) * XP_PER_REPETITION
        return review_xp + len(sessions) * XP_PER_EXAM

    def _streak_days(self, cards: List[Card]) -> int:
        """
        Consecutive days up to today on which at least one card was touched.

        Approximated from `Card.updated_at` because no per-review history table
        exists — a card reviewed twice in one day counts once, and a card edited
        (rather than reviewed) also counts. Good enough for a streak badge;
        replace with a real review-log query if the number ever needs to be
        authoritative.
        """
        active_days = {c.updated_at.date() for c in cards if c.srs_repetitions > 0}
        if not active_days:
            return 0

        today = date.today()
        # A streak stays alive if the last activity was today or yesterday.
        cursor = today if today in active_days else today - timedelta(days=1)
        if cursor not in active_days:
            return 0

        streak = 0
        while cursor in active_days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def _exam_readiness(self, sessions: List[ExamSession]) -> int:
        if not sessions:
            return 0
        recent = sorted(sessions, key=lambda s: s.started_at, reverse=True)[
            :READINESS_WINDOW
        ]
        return round(sum(s.score for s in recent) / len(recent))

    def _worlds(self, decks: List[Deck], cards: List[Card]) -> List[Dict[str, Any]]:
        """One world per deck; each world's levels are chunks of LEVEL_SIZE cards."""
        worlds: List[Dict[str, Any]] = []

        for deck in decks:
            deck_cards = sorted(
                (c for c in cards if c.deck_id == deck.id),
                key=lambda c: (c.position, c.created_at),
            )
            if not deck_cards:
                continue

            chunks = [
                deck_cards[i : i + LEVEL_SIZE]
                for i in range(0, len(deck_cards), LEVEL_SIZE)
            ]

            levels: List[Dict[str, Any]] = []
            seen_current = False
            for index, chunk in enumerate(chunks, start=1):
                done = all(c.srs_repetitions > 0 for c in chunk)
                if done:
                    status = "done"
                elif not seen_current:
                    status = "current"
                    seen_current = True
                else:
                    status = "locked"
                levels.append(
                    {"id": f"{deck.id}-{index}", "index": index, "status": status}
                )

            learned = sum(1 for c in deck_cards if c.srs_repetitions > 0)
            worlds.append(
                {
                    "id": str(deck.id),
                    "title": deck.name,
                    "levels": levels,
                    "progressPercent": round(learned / len(deck_cards) * 100),
                    # Language-neutral on purpose: the frontend owns copy, this
                    # endpoint must not hardcode VI or EN text.
                    "subLabel": f"{learned}/{len(deck_cards)}",
                }
            )

        return worlds
