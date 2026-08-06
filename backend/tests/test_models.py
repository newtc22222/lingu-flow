import uuid
from datetime import datetime, timezone
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import (
    User,
    Deck,
    Card,
    ExamTemplate,
    ExamTemplateQuestion,
    Question,
    ExamSession,
    AnswerRecord,
)


@pytest.mark.asyncio
async def test_user_model_creation(db_session: AsyncSession):
    """Test creating a User and fetching from DB."""
    user = User(
        username="teststudent",
        email="student@linguflow.com",
        password_hash="hashed_pw_123",
        is_guest=False,
        daily_streak=5,
    )
    db_session.add(user)
    await db_session.commit()

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)

    result = await db_session.execute(select(User).where(User.username == "teststudent"))
    fetched_user = result.scalar_one_or_none()
    assert fetched_user is not None
    assert fetched_user.email == "student@linguflow.com"
    assert fetched_user.daily_streak == 5
    assert fetched_user.is_guest is False


@pytest.mark.asyncio
async def test_deck_and_card_models(db_session: AsyncSession):
    """Test Deck & Card models, foreign keys, and relationships."""
    user = User(username="deck_owner", email="deck@test.com")
    db_session.add(user)
    await db_session.commit()

    deck = Deck(user_id=user.id, name="TOEIC Vocabulary", description="Essential TOEIC words")
    db_session.add(deck)
    await db_session.commit()

    card = Card(
        user_id=user.id,
        deck_id=deck.id,
        front="negotiation",
        back="**discussion aimed at reaching an agreement**",
        srs_interval=1,
        srs_ease_factor=2.5,
        srs_repetitions=1,
    )
    db_session.add(card)
    await db_session.commit()

    assert card.id is not None
    assert card.deck_id == deck.id
    assert card.srs_ease_factor == 2.5

    result = await db_session.execute(select(Card).where(Card.id == card.id))
    fetched_card = result.scalar_one()
    assert fetched_card.front == "negotiation"


@pytest.mark.asyncio
async def test_exam_template_and_question_models(db_session: AsyncSession):
    """Test ExamTemplate and Question models with JSON options."""
    template = ExamTemplate(
        name="JLPT N5 Mini Test",
        exam_type="jlpt",
        description="Basic Japanese vocabulary and grammar",
        duration_minutes=25,
        total_questions=1,
        passing_score=60,
        level="N5",
        is_public=True,
        tags=["jlpt", "n5"],
    )
    db_session.add(template)
    await db_session.commit()

    question = Question(
        exam_type="jlpt",
        part="language-knowledge",
        question_text="わたしは まいにち コーヒー _____ のみます。",
        type="multiple-choice",
        options=["A. は", "B. が", "C. を", "D. に"],
        correct_answer="C",
        explanation="を is the direct object marker.",
        difficulty="easy",
    )
    db_session.add(question)
    await db_session.flush()

    # Placement in an exam is a join row, not a column on the question.
    db_session.add(
        ExamTemplateQuestion(
            exam_template_id=template.id,
            question_id=question.id,
            order_index=0,
        )
    )
    await db_session.commit()

    assert question.id is not None
    assert len(question.options) == 4
    assert question.options[2] == "C. を"

    result = await db_session.execute(
        select(ExamTemplate).where(ExamTemplate.id == template.id)
    )
    fetched_template = result.scalar_one()
    assert fetched_template.name == "JLPT N5 Mini Test"
    assert fetched_template.is_public is True


@pytest.mark.asyncio
async def test_exam_session_and_answer_record_models(db_session: AsyncSession):
    """Test ExamSession and AnswerRecord tracking models."""
    user = User(username="exam_taker", email="taker@test.com")
    template = ExamTemplate(
        name="TOEIC Part 5",
        exam_type="toeic",
        duration_minutes=20,
        total_questions=1,
        is_public=True,
    )
    db_session.add_all([user, template])
    await db_session.commit()

    question = Question(
        exam_type="toeic",
        part="part5",
        question_text="The project manager asked that all reports _____ submitted by Friday.",
        options=["A. are", "B. be", "C. were", "D. being"],
        correct_answer="B",
    )
    db_session.add(question)
    await db_session.flush()
    db_session.add(
        ExamTemplateQuestion(
            exam_template_id=template.id,
            question_id=question.id,
            order_index=0,
        )
    )
    await db_session.commit()

    session = ExamSession(
        user_id=user.id,
        exam_template_id=template.id,
        time_limit_minutes=20,
        score=100.0,
        correct_count=1,
        total_count=1,
        status="completed",
    )
    db_session.add(session)
    await db_session.commit()

    answer = AnswerRecord(
        session_id=session.id,
        question_id=question.id,
        user_answer="B",
        is_correct=True,
        time_taken_seconds=15,
    )
    db_session.add(answer)
    await db_session.commit()

    assert session.id is not None
    assert answer.session_id == session.id
    assert answer.is_correct is True
    assert answer.user_answer == "B"
