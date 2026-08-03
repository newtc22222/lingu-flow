import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import ExamTemplate, Question
from app.routers.events import event_generator
from app.seed.exam_seed import seed_builtin_exams


@pytest.mark.asyncio
async def test_builtin_exam_seeding(db_session: AsyncSession):
    """Test seeding 33 built-in certification exam questions across 4 templates."""
    # 1. Run seed
    await seed_builtin_exams(db_session)

    # 2. Check 4 templates exist
    t_res = await db_session.execute(
        select(ExamTemplate).where(ExamTemplate.is_public == True)
    )
    templates = t_res.scalars().all()
    assert len(templates) == 4

    # 3. Check questions count = 33
    q_res = await db_session.execute(select(Question))
    questions = q_res.scalars().all()
    assert len(questions) == 33

    # 4. Run seed second time to verify idempotency
    await seed_builtin_exams(db_session)
    t_res2 = await db_session.execute(
        select(ExamTemplate).where(ExamTemplate.is_public == True)
    )
    assert len(t_res2.scalars().all()) == 4


@pytest.mark.asyncio
async def test_sse_events_generator():
    """Test SSE event_generator output."""
    class DummyRequest:
        async def is_disconnected(self):
            return True  # Exit loop immediately after first yield

    gen = event_generator(DummyRequest(), user_id="test_user_123")
    first_event = await anext(gen)

    assert first_event["event"] == "connected"
    assert "test_user_123" in first_event["data"]
