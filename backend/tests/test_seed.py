from collections import Counter

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import ExamTemplate, ExamTemplateQuestion, Question
from app.seed.exam_seed import BUILTIN_SEED_DATA, seed_builtin_exams

# Derived, not hardcoded: the counts move whenever seed content is authored,
# and a test that has to be edited alongside the content it guards stops
# guarding anything.
EXPECTED_TEMPLATES = len(BUILTIN_SEED_DATA)
EXPECTED_QUESTIONS = sum(len(t["questions"]) for t in BUILTIN_SEED_DATA)


@pytest.mark.asyncio
async def test_builtin_exam_seeding(db_session: AsyncSession):
    """Seeds every built-in template with its questions, and is idempotent."""
    await seed_builtin_exams(db_session)

    t_res = await db_session.execute(
        select(ExamTemplate).where(ExamTemplate.is_public.is_(True))
    )
    templates = t_res.scalars().all()
    assert len(templates) == EXPECTED_TEMPLATES
    # Every built-in carries a stable seed identity for later content updates.
    assert all(t.seed_key and t.seed_version for t in templates)

    q_res = await db_session.execute(select(Question))
    assert len(q_res.scalars().all()) == EXPECTED_QUESTIONS

    # Questions reach their exam through the junction, not an ownership FK.
    link_res = await db_session.execute(select(ExamTemplateQuestion))
    assert len(link_res.scalars().all()) == EXPECTED_QUESTIONS

    # Re-running at the same version changes nothing.
    await seed_builtin_exams(db_session)
    t_res2 = await db_session.execute(
        select(ExamTemplate).where(ExamTemplate.is_public.is_(True))
    )
    assert len(t_res2.scalars().all()) == EXPECTED_TEMPLATES
    q_res2 = await db_session.execute(select(Question))
    assert len(q_res2.scalars().all()) == EXPECTED_QUESTIONS


@pytest.mark.asyncio
async def test_toeic_reading_covers_all_three_parts(db_session: AsyncSession):
    """
    The TOEIC set must exercise every structural path, not just Part 5.

    Parts 6 and 7 are what make `passage_group` load-bearing: their questions
    share one passage, and attaching only part of such a set produces a broken
    exam.
    """
    await seed_builtin_exams(db_session)

    toeic = (
        await db_session.execute(
            select(Question).where(Question.exam_type == "toeic")
        )
    ).scalars().all()

    by_part = Counter(q.part for q in toeic)
    assert by_part["part5"] >= 10
    assert by_part["part6"] >= 4
    assert by_part["part7"] >= 10

    # Part 5 is standalone; Parts 6 and 7 are always grouped around a passage.
    assert all(q.passage_group is None for q in toeic if q.part == "part5")
    grouped = [q for q in toeic if q.part in ("part6", "part7")]
    assert grouped and all(q.passage_group and q.passage for q in grouped)

    # Every group holds more than one question, or it wouldn't be a set.
    group_sizes = Counter(q.passage_group for q in grouped)
    assert all(size > 1 for size in group_sizes.values())

    # Tags drive the per-category results breakdown, so none may be untagged.
    assert all(q.tags for q in toeic)


@pytest.mark.asyncio
async def test_seed_version_bump_updates_in_place(monkeypatch, db_session: AsyncSession):
    """
    A content update must reuse the template row rather than adding a second one.

    The template id has to survive: past ExamSessions reference it, so creating
    a replacement would strand their history behind a dead foreign key.
    """
    await seed_builtin_exams(db_session)

    original = (
        await db_session.execute(
            select(ExamTemplate).where(
                ExamTemplate.seed_key == BUILTIN_SEED_DATA[0]["seedKey"]
            )
        )
    ).scalar_one()
    original_id = original.id

    bumped = [dict(BUILTIN_SEED_DATA[0])]
    # Derived, not hardcoded: content versions move as seed data is authored,
    # and a literal here would silently start matching and skip the update.
    bumped_version = f"{BUILTIN_SEED_DATA[0]['seedVersion']}-bumped"
    bumped[0]["seedVersion"] = bumped_version
    bumped[0]["questions"] = [
        {
            "questionText": "A replacement question.",
            "options": ["A. one", "B. two", "C. three", "D. four"],
            "correctAnswer": "A",
            "part": "part5",
        }
    ]
    monkeypatch.setattr("app.seed.exam_seed.BUILTIN_SEED_DATA", bumped)

    await seed_builtin_exams(db_session)

    updated = (
        await db_session.execute(
            select(ExamTemplate).where(ExamTemplate.seed_key == bumped[0]["seedKey"])
        )
    ).scalars().all()
    assert len(updated) == 1, "a version bump must not create a second template"
    assert updated[0].id == original_id
    assert updated[0].seed_version == bumped_version
    assert updated[0].total_questions == 1

    # The replaced questions are archived, not deleted — past sessions'
    # answer records still point at them.
    archived = (
        await db_session.execute(
            select(Question).where(Question.archived_at.is_not(None))
        )
    ).scalars().all()
    assert len(archived) == len(BUILTIN_SEED_DATA[0]["questions"])
