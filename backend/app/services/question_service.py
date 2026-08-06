import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import ExamTemplate, ExamTemplateQuestion, Question
from app.schemas.exam import QuestionCreateRequest, QuestionUpdateRequest

# Options are stored pre-prefixed ("A. Paris") because the exam UI and the
# seeded content both assume it. Normalizing here means an API-authored
# question can't skip the prefix and render as bare text next to prefixed ones.
OPTION_KEYS = ("A", "B", "C", "D")


def normalize_options(options: List[str]) -> List[str]:
    """Ensure every option carries its positional letter prefix exactly once."""
    normalized = []
    for index, option in enumerate(options):
        text = option.strip()
        if index < len(OPTION_KEYS):
            prefix = f"{OPTION_KEYS[index]}. "
            # Strip any existing (possibly wrong) prefix before re-applying, so
            # reordered options don't end up labelled with a stale letter.
            for key in OPTION_KEYS:
                if text.upper().startswith(f"{key}."):
                    text = text[len(key) + 1 :].strip()
                    break
            text = prefix + text
        normalized.append(text)
    return normalized


async def sync_total_questions(db: AsyncSession, template_id: uuid.UUID) -> None:
    """
    Recompute a template's denormalized `total_questions` from the junction.

    Shared by every composition mutation so the counter can't drift — there are
    six write paths that change a composition, and hand-maintained += / -=
    arithmetic at each was a bug waiting to happen.
    """
    count = await db.scalar(
        select(func.count())
        .select_from(ExamTemplateQuestion)
        .where(ExamTemplateQuestion.exam_template_id == template_id)
    )
    template = (
        await db.execute(select(ExamTemplate).where(ExamTemplate.id == template_id))
    ).scalar_one_or_none()
    if template:
        template.total_questions = count or 0


class QuestionService:
    """The question bank, independent of any exam template."""

    async def _answer_count(self, db: AsyncSession, question_id: uuid.UUID) -> int:
        from app.models.session import AnswerRecord

        return (
            await db.scalar(
                select(func.count())
                .select_from(AnswerRecord)
                .where(AnswerRecord.question_id == question_id)
            )
        ) or 0

    async def list_questions(
        self,
        db: AsyncSession,
        exam_type: Optional[str] = None,
        part: Optional[str] = None,
        tags: Optional[List[str]] = None,
        difficulty: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Question]:
        """Browse the bank. Archived questions are never listed."""
        stmt = select(Question).where(Question.archived_at.is_(None))

        if exam_type:
            stmt = stmt.where(Question.exam_type == exam_type)
        if part:
            stmt = stmt.where(Question.part == part)
        if difficulty:
            stmt = stmt.where(Question.difficulty == difficulty)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Question.question_text.ilike(pattern),
                    Question.passage.ilike(pattern),
                )
            )

        stmt = stmt.order_by(Question.created_at.desc(), Question.id.asc())

        if not tags:
            return list((await db.execute(stmt.limit(limit).offset(offset))).scalars().all())

        # Tag matching happens in Python: `tags` is a JSON column and the
        # containment operators differ between Postgres (jsonb ?/@>) and the
        # SQLite used by the test suite. Fine at bank sizes in the hundreds —
        # revisit with a question_tags join table past a few thousand rows.
        wanted = {t.lower() for t in tags}
        matched = [
            q
            for q in (await db.execute(stmt)).scalars().all()
            if wanted.issubset({t.lower() for t in (q.tags or [])})
        ]
        return matched[offset : offset + limit]

    async def get_question(
        self, db: AsyncSession, question_id: uuid.UUID
    ) -> Optional[Question]:
        return (
            await db.execute(
                select(Question).where(
                    Question.id == question_id, Question.archived_at.is_(None)
                )
            )
        ).scalar_one_or_none()

    async def create_question(
        self, db: AsyncSession, user_id: uuid.UUID, req: QuestionCreateRequest
    ) -> Question:
        """Create a standalone bank question, attached to no exam."""
        question = Question(
            user_id=user_id,
            exam_type=req.exam_type,
            part=req.part,
            passage_group=req.passage_group,
            question_text=req.question_text,
            passage=req.passage,
            type=req.type,
            options=normalize_options(req.options),
            correct_answer=req.correct_answer,
            explanation=req.explanation,
            tags=req.tags or [],
            difficulty=req.difficulty,
        )
        db.add(question)
        await db.commit()
        await db.refresh(question)
        return question

    async def update_question(
        self,
        db: AsyncSession,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
        req: QuestionUpdateRequest,
    ) -> Optional[Question]:
        """
        Update a question the user owns.

        Once answered, options and the correct answer are frozen: changing them
        would leave every stored `is_correct` disagreeing with the displayed
        key, so past results would quietly start lying. Wording, explanation,
        tags and difficulty stay editable.
        """
        question = (
            await db.execute(
                select(Question).where(
                    Question.id == question_id,
                    Question.user_id == user_id,
                    Question.archived_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if not question:
            return None

        options = normalize_options(req.options)
        answer_key_changed = (
            list(options) != list(question.options)
            or req.correct_answer != question.correct_answer
        )
        if answer_key_changed and await self._answer_count(db, question_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This question has already been answered; its options and "
                    "correct answer can no longer be changed."
                ),
            )

        question.exam_type = req.exam_type
        question.part = req.part
        question.passage_group = req.passage_group
        question.question_text = req.question_text
        question.passage = req.passage
        question.type = req.type
        question.options = options
        question.correct_answer = req.correct_answer
        question.explanation = req.explanation
        question.difficulty = req.difficulty
        if req.tags is not None:
            question.tags = req.tags

        await db.commit()
        await db.refresh(question)
        return question

    async def delete_question(
        self,
        db: AsyncSession,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
        hard: bool = False,
    ) -> bool:
        """
        Archive a question the user owns and detach it from every exam.

        Soft, because `AnswerRecord.question_id` cascades: a hard delete erases
        the answer history of every past session that used the question,
        leaving finished sessions with a stored score but nothing to show.
        """
        question = (
            await db.execute(
                select(Question).where(
                    Question.id == question_id, Question.user_id == user_id
                )
            )
        ).scalar_one_or_none()
        if not question:
            return False

        if hard and await self._answer_count(db, question_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This question has been answered; hard-deleting it would "
                    "destroy session history. Delete it normally to archive it."
                ),
            )

        affected = list(
            (
                await db.execute(
                    select(ExamTemplateQuestion.exam_template_id).where(
                        ExamTemplateQuestion.question_id == question_id
                    )
                )
            ).scalars().all()
        )
        await db.execute(
            delete(ExamTemplateQuestion).where(
                ExamTemplateQuestion.question_id == question_id
            )
        )
        if hard:
            await db.delete(question)
        else:
            question.archived_at = datetime.now(timezone.utc)

        await db.flush()
        for template_id in set(affected):
            await sync_total_questions(db, template_id)

        await db.commit()
        return True

    async def list_tags(
        self,
        db: AsyncSession,
        exam_type: Optional[str] = None,
        part: Optional[str] = None,
    ) -> List[str]:
        """Distinct tags across the live bank, for filter autocomplete."""
        stmt = select(Question.tags).where(Question.archived_at.is_(None))
        if exam_type:
            stmt = stmt.where(Question.exam_type == exam_type)
        if part:
            stmt = stmt.where(Question.part == part)

        seen: set[str] = set()
        for tags in (await db.execute(stmt)).scalars().all():
            seen.update(tags or [])
        return sorted(seen)

    async def list_parts(
        self, db: AsyncSession, exam_type: Optional[str] = None
    ) -> List[str]:
        """Distinct non-null parts across the live bank."""
        stmt = (
            select(Question.part)
            .where(Question.archived_at.is_(None), Question.part.is_not(None))
            .distinct()
        )
        if exam_type:
            stmt = stmt.where(Question.exam_type == exam_type)
        return sorted(p for p in (await db.execute(stmt)).scalars().all() if p)
