"""
Postgres integrity suite (F-08 / Horizon A4).

These tests exercise cascade semantics and real commit boundaries that SQLite
silently skips. They are excluded from the default run (`addopts = -m "not
postgres"`). See tests/README.md for how to run them locally and in CI.
"""
from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import ExamTemplate, ExamTemplateQuestion, Question
from app.models.session import AnswerRecord, ExamSession
from app.models.user import User
from app.services.exam_service import ExamService
from tests.postgres.conftest import unique_name

pytestmark = pytest.mark.postgres

exam_service = ExamService()


async def _register(client: AsyncClient, name: str) -> dict:
    res = await client.post(
        "/api/auth/register",
        json={
            "username": name,
            "email": f"{name}@linguflow.test",
            "password": "Password123!",
        },
    )
    assert res.status_code == 201, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


async def _create_template_with_question(
    client: AsyncClient, headers: dict, *, public: bool = False
) -> tuple[str, str]:
    t = await client.post(
        "/api/exams/templates",
        json={
            "name": unique_name("tmpl"),
            "examType": "custom",
            "durationMinutes": 15,
            "isPublic": public,
        },
        headers=headers,
    )
    assert t.status_code == 201, t.text
    template_id = t.json()["id"]

    q = await client.post(
        f"/api/exams/templates/{template_id}/questions",
        json={
            "examType": "custom",
            "questionText": "Integrity probe?",
            "options": ["A. one", "B. two", "C. three", "D. four"],
            "correctAnswer": "A",
            "explanation": "Because A.",
        },
        headers=headers,
    )
    assert q.status_code == 201, q.text
    return template_id, q.json()["id"]


# ─── Schema / constraints ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_seed_key_unique_constraint(pg_session: AsyncSession):
    """Alembic unique index on exam_templates.seed_key is enforced by Postgres."""
    a = ExamTemplate(
        name="Seeded A",
        exam_type="toeic",
        duration_minutes=10,
        seed_key="unique_probe",
        seed_version="1",
        is_public=True,
    )
    b = ExamTemplate(
        name="Seeded B",
        exam_type="toeic",
        duration_minutes=10,
        seed_key="unique_probe",
        seed_version="2",
        is_public=True,
    )
    pg_session.add(a)
    await pg_session.flush()
    pg_session.add(b)
    with pytest.raises(IntegrityError):
        await pg_session.flush()
    await pg_session.rollback()


# ─── Soft delete vs hard cascade ──────────────────────────────────────────────
@pytest.mark.asyncio
async def test_soft_delete_keeps_answer_history_resolvable(
    pg_client: AsyncClient, pg_session: AsyncSession
):
    """
    After a soft-delete, past sessions still resolve the question row.

    Hard-delete would CASCADE from questions → answer_records and erase history;
    that is exactly why the bank uses archived_at.
    """
    headers = await _register(pg_client, unique_name("soft"))
    template_id, question_id = await _create_template_with_question(pg_client, headers)

    session_res = await pg_client.post(
        "/api/exams/sessions",
        json={"examTemplateId": template_id},
        headers=headers,
    )
    assert session_res.status_code == 201
    session_id = session_res.json()["id"]
    assert (
        await pg_client.put(
            f"/api/exams/sessions/{session_id}/finish", headers=headers
        )
    ).status_code == 200

    # Soft-delete via API (sets archived_at, detaches links).
    del_res = await pg_client.delete(
        f"/api/questions/{question_id}", headers=headers
    )
    assert del_res.status_code in (200, 204)

    q = await pg_session.get(Question, uuid.UUID(question_id))
    assert q is not None
    assert q.archived_at is not None

    ar = (
        await pg_session.execute(
            select(AnswerRecord).where(
                AnswerRecord.session_id == uuid.UUID(session_id),
                AnswerRecord.question_id == uuid.UUID(question_id),
            )
        )
    ).scalar_one()
    assert ar is not None

    details = await pg_client.get(
        f"/api/exams/sessions/{session_id}/details", headers=headers
    )
    assert details.status_code == 200
    body = details.json()
    assert any(q["id"] == question_id for q in body["questions"])


@pytest.mark.asyncio
async def test_delete_template_removes_links_not_questions(
    pg_client: AsyncClient, pg_session: AsyncSession
):
    """Template delete must drop junction rows only — bank questions survive."""
    headers = await _register(pg_client, unique_name("tmpl_del"))
    template_id, question_id = await _create_template_with_question(pg_client, headers)

    del_res = await pg_client.delete(
        f"/api/exams/templates/{template_id}", headers=headers
    )
    assert del_res.status_code in (200, 204)

    assert await pg_session.get(ExamTemplate, uuid.UUID(template_id)) is None
    links = (
        await pg_session.execute(
            select(ExamTemplateQuestion).where(
                ExamTemplateQuestion.question_id == uuid.UUID(question_id)
            )
        )
    ).scalars().all()
    assert links == []

    q = await pg_session.get(Question, uuid.UUID(question_id))
    assert q is not None
    assert q.archived_at is None


# ─── Dual-commit create_session (documents F-04 until A5 lands) ───────────────
@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=True,
    reason=(
        "F-04 / #48: create_session commits the ExamSession before AnswerRecords. "
        "A crash between those commits leaves an unplayable session. Remove this "
        "xfail when services stop mid-request committing (A5)."
    ),
)
async def test_create_session_is_atomic_under_midway_failure(
    pg_session: AsyncSession,
):
    """
    Inject a failure after the session row is committed but before answer
    records land. Atomic create_session must leave zero orphan sessions.
    """
    user = User(
        username=unique_name("u"),
        email=f"{unique_name('e')}@linguflow.test",
        password_hash="x",
        is_guest=False,
    )
    template = ExamTemplate(
        name=unique_name("atomic"),
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
    pg_session.add_all([user, template, question])
    await pg_session.flush()
    pg_session.add(
        ExamTemplateQuestion(
            exam_template_id=template.id,
            question_id=question.id,
            order_index=0,
        )
    )
    await pg_session.commit()

    original_commit = AsyncSession.commit
    commits = {"n": 0}

    async def flaky_commit(self):  # type: ignore[no-untyped-def]
        # create_session does: commit(session row) then commit(answer records).
        # Fail on the second service-level commit so the session row is durable
        # but answer rows are not — the dual-commit bug.
        commits["n"] += 1
        if commits["n"] == 2:
            raise RuntimeError("injected failure between session and answer commits")
        return await original_commit(self)

    # Bind the flaky commit only for this probe.
    AsyncSession.commit = flaky_commit  # type: ignore[method-assign]
    try:
        with pytest.raises(RuntimeError, match="injected failure"):
            await exam_service.create_session(pg_session, user.id, template.id)
    finally:
        AsyncSession.commit = original_commit  # type: ignore[method-assign]

    # Use a fresh lookup after the failed unit of work.
    await pg_session.rollback()
    orphan_sessions = (
        await pg_session.execute(
            select(ExamSession).where(ExamSession.user_id == user.id)
        )
    ).scalars().all()
    orphan_answers = (
        await pg_session.execute(select(AnswerRecord))
    ).scalars().all()

    # Desired invariant (fails today under dual commit → xfail until A5):
    assert orphan_sessions == [], (
        f"expected no session after midway failure, found {len(orphan_sessions)} "
        f"(answers={len(orphan_answers)})"
    )
