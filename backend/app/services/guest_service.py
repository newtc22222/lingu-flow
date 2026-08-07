import logging
from datetime import timedelta
from typing import List, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.timeutils import utcnow
from app.models.exam import ExamTemplate
from app.models.session import ExamSession
from app.models.user import User

logger = logging.getLogger("linguflow")
settings = get_settings()


async def _release_guest_templates(db: AsyncSession, guest: User) -> None:
    """Deal with exam templates a departing guest owns.

    `exam_templates.user_id` is ON DELETE SET NULL, and `ExamService.get_templates`
    treats an ownerless public template as a built-in. Left alone, a deleted
    guest's public template would therefore surface to *every* user as though it
    had been seeded. So ownership is never simply dropped:

    - if anyone else has sat the exam, the template is kept but unpublished, since
      hard-deleting it would cascade away another user's finished session; this
      matches the rule that a finished session's results must stay resolvable.
    - otherwise nothing references it and it is deleted outright.
    """
    result = await db.execute(
        select(ExamTemplate).where(ExamTemplate.user_id == guest.id)
    )
    templates: Sequence[ExamTemplate] = result.scalars().all()

    for template in templates:
        foreign_session = await db.execute(
            select(ExamSession.id)
            .where(
                ExamSession.exam_template_id == template.id,
                ExamSession.user_id != guest.id,
            )
            .limit(1)
        )
        if foreign_session.scalar_one_or_none() is not None:
            template.user_id = None
            template.is_public = False
        else:
            await db.delete(template)


async def purge_guest_user(db: AsyncSession, guest: User) -> None:
    """Remove a guest and everything that belongs only to them.

    Uses ORM deletes rather than a bulk statement on purpose: `User.decks`,
    `User.cards` and `User.exam_sessions` carry `cascade="all, delete-orphan"`,
    which works on any engine, whereas DB-level ON DELETE CASCADE silently does
    nothing under SQLite (foreign keys are off by default there) — so the tests
    would pass while proving nothing.

    Questions authored by the guest are intentionally left behind: the bank is
    shared and global, and hard-deleting a question would cascade away the
    AnswerRecord history of every session that ever used it.

    Does not commit — the caller owns the transaction boundary.
    """
    await _release_guest_templates(db, guest)
    await db.delete(guest)


async def cleanup_inactive_guests(
    db: AsyncSession, batch_size: int = 500
) -> int:
    """Delete guest accounts idle for longer than the retention window.

    Returns the number of guests removed. Commits per batch so a large sweep
    never sits in one long transaction.
    """
    cutoff = utcnow() - timedelta(days=settings.GUEST_RETENTION_DAYS)
    total = 0

    while True:
        result = await db.execute(
            select(User)
            .where(User.is_guest.is_(True), User.last_active < cutoff)
            .limit(batch_size)
        )
        guests: List[User] = list(result.scalars().all())
        if not guests:
            break

        for guest in guests:
            await purge_guest_user(db, guest)
        await db.commit()
        total += len(guests)

        if len(guests) < batch_size:
            break

    logger.info(
        "Guest cleanup: removed %d inactive guest account(s) "
        "(idle since before %s, retention %d days)",
        total,
        cutoff.isoformat(),
        settings.GUEST_RETENTION_DAYS,
    )
    return total
