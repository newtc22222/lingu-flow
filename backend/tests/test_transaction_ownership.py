"""Service methods must not commit; get_db / the caller owns the boundary."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import ExamTemplate, ExamTemplateQuestion, Question
from app.models.session import AnswerRecord, ExamSession
from app.models.user import User
from app.services.exam_service import ExamService

exam_service = ExamService()


@pytest.mark.asyncio
async def test_create_session_midway_failure_leaves_no_orphan(db_session: AsyncSession):
    """
    After the session row is flushed, a failure before answer rows must roll
    back cleanly — no durable ExamSession without AnswerRecords.
    """
    user = User(
        username=f"tx_{uuid.uuid4().hex[:8]}",
        email=f"tx_{uuid.uuid4().hex[:8]}@test.local",
        password_hash="x",
        is_guest=False,
    )
    template = ExamTemplate(
        name="tx-atomic",
        exam_type="custom",
        duration_minutes=10,
        is_public=True,
        total_questions=1,
    )
    question = Question(
        exam_type="custom",
        question_text="Atomic?",
        type="multiple-choice",
        options=["A. a", "B. b", "C. c", "D. d"],
        correct_answer="A",
    )
    db_session.add_all([user, template, question])
    await db_session.flush()
    db_session.add(
        ExamTemplateQuestion(
            exam_template_id=template.id,
            question_id=question.id,
            order_index=0,
        )
    )
    await db_session.commit()
    user_id = user.id
    template_id = template.id

    original_add_all = AsyncSession.add_all

    def boom_add_all(self, instances):  # type: ignore[no-untyped-def]
        raise RuntimeError("injected failure after session flush")

    AsyncSession.add_all = boom_add_all  # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError, match="injected failure"):
            await exam_service.create_session(db_session, user_id, template_id)
    finally:
        AsyncSession.add_all = original_add_all  # type: ignore[method-assign]

    await db_session.rollback()
    sessions = (
        await db_session.execute(
            select(ExamSession).where(ExamSession.user_id == user_id)
        )
    ).scalars().all()
    answers = (await db_session.execute(select(AnswerRecord))).scalars().all()
    assert sessions == []
    assert answers == []
