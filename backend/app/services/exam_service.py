import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import ExamTemplate, ExamTemplateQuestion, Question
from app.models.session import AnswerRecord, ExamSession
from app.services.question_service import (
    QuestionService,
    normalize_options,
    sync_total_questions,
)
from app.schemas.exam import (
    ExamSessionCreateRequest,
    ExamTemplateCreateRequest,
    ExamTemplateUpdateRequest,
    QuestionCreateRequest,
    QuestionUpdateRequest,
    SubmitAnswerRequest,
)


question_service = QuestionService()


class ExamService:
    # ─── TEMPLATES ───────────────────────────────────────────────
    async def get_templates(
        self, db: AsyncSession, user_id: Optional[uuid.UUID] = None
    ) -> List[ExamTemplate]:
        """Fetch all public templates plus custom templates owned by user."""
        conditions = [ExamTemplate.is_public == True]
        if user_id:
            conditions.append(ExamTemplate.user_id == user_id)

        stmt = select(ExamTemplate).where(or_(*conditions)).order_by(ExamTemplate.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_parts_by_template(
        self, db: AsyncSession, template_ids: List[uuid.UUID]
    ) -> Dict[uuid.UUID, List[str]]:
        """
        Distinct question parts per template, in one query.

        Parts are a property of questions, but the exam hub filters templates by
        them — so they have to be rolled up here rather than stored.
        """
        if not template_ids:
            return {}

        rows = (
            await db.execute(
                select(ExamTemplateQuestion.exam_template_id, Question.part)
                .join(Question, Question.id == ExamTemplateQuestion.question_id)
                .where(
                    ExamTemplateQuestion.exam_template_id.in_(template_ids),
                    Question.part.is_not(None),
                )
                .distinct()
            )
        ).all()

        grouped: Dict[uuid.UUID, List[str]] = {}
        for template_id, part in rows:
            grouped.setdefault(template_id, []).append(part)
        return {key: sorted(value) for key, value in grouped.items()}

    async def get_template_by_id(
        self, db: AsyncSession, template_id: uuid.UUID
    ) -> Optional[ExamTemplate]:
        """Fetch exam template by ID."""
        result = await db.execute(
            select(ExamTemplate).where(ExamTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def create_template(
        self, db: AsyncSession, user_id: uuid.UUID, req: ExamTemplateCreateRequest
    ) -> ExamTemplate:
        """Create a custom exam template."""
        template = ExamTemplate(
            user_id=user_id,
            name=req.name,
            exam_type=req.exam_type,
            description=req.description,
            duration_minutes=req.duration_minutes,
            passing_score=req.passing_score,
            level=req.level,
            is_public=req.is_public,
            tags=req.tags or [],
            total_questions=0,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    async def update_template(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        req: ExamTemplateUpdateRequest,
    ) -> Optional[ExamTemplate]:
        """
        Update a custom template owned by the user.

        Built-in public templates are intentionally not editable — the seed
        re-runs on every startup and would clobber any edit anyway.
        """
        result = await db.execute(
            select(ExamTemplate).where(
                ExamTemplate.id == template_id,
                ExamTemplate.user_id == user_id,
                ExamTemplate.is_public == False,
            )
        )
        template = result.scalar_one_or_none()
        if not template:
            return None

        template.name = req.name
        template.exam_type = req.exam_type
        template.description = req.description
        template.duration_minutes = req.duration_minutes
        template.passing_score = req.passing_score
        template.level = req.level
        if req.tags is not None:
            template.tags = req.tags

        await db.commit()
        await db.refresh(template)
        return template

    async def delete_template(
        self, db: AsyncSession, template_id: uuid.UUID, user_id: uuid.UUID
    ) -> bool:
        """Delete custom template owned by user."""
        result = await db.execute(
            select(ExamTemplate).where(
                ExamTemplate.id == template_id,
                ExamTemplate.user_id == user_id,
                ExamTemplate.is_public == False,
            )
        )
        template = result.scalar_one_or_none()
        if not template:
            return False

        await db.delete(template)
        await db.commit()
        return True

    # ─── COMPOSITION ─────────────────────────────────────────────
    async def _sync_total_questions(
        self, db: AsyncSession, template_id: uuid.UUID
    ) -> None:
        """Delegates to the shared helper (see question_service)."""
        await sync_total_questions(db, template_id)

    async def get_questions(
        self, db: AsyncSession, template_id: uuid.UUID
    ) -> List[Question]:
        """Fetch a template's questions in composition order."""
        stmt = (
            select(Question)
            .join(
                ExamTemplateQuestion,
                ExamTemplateQuestion.question_id == Question.id,
            )
            .where(ExamTemplateQuestion.exam_template_id == template_id)
            # Secondary sort on id keeps output stable when two links somehow
            # share an order_index.
            .order_by(ExamTemplateQuestion.order_index.asc(), Question.id.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_questions_with_order(
        self, db: AsyncSession, template_id: uuid.UUID
    ) -> List[Tuple[Question, int]]:
        """As `get_questions`, but pairs each question with its order_index."""
        stmt = (
            select(Question, ExamTemplateQuestion.order_index)
            .join(
                ExamTemplateQuestion,
                ExamTemplateQuestion.question_id == Question.id,
            )
            .where(ExamTemplateQuestion.exam_template_id == template_id)
            .order_by(ExamTemplateQuestion.order_index.asc(), Question.id.asc())
        )
        result = await db.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def _owned_template_or_404(
        self, db: AsyncSession, template_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExamTemplate:
        """
        Resolve a template the user may compose, or raise 404.

        Built-in public templates are excluded: the startup seed owns them and
        would overwrite any edit. (`add_question` previously had no ownership
        check at all, so any authenticated user could add questions to any
        built-in exam.)
        """
        result = await db.execute(
            select(ExamTemplate).where(
                ExamTemplate.id == template_id,
                ExamTemplate.user_id == user_id,
                ExamTemplate.is_public == False,  # noqa: E712
            )
        )
        template = result.scalar_one_or_none()
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found or not editable",
            )
        return template

    async def _next_order_index(
        self, db: AsyncSession, template_id: uuid.UUID
    ) -> int:
        current_max = await db.scalar(
            select(func.max(ExamTemplateQuestion.order_index)).where(
                ExamTemplateQuestion.exam_template_id == template_id
            )
        )
        return 0 if current_max is None else current_max + 1

    async def add_question(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        req: QuestionCreateRequest,
    ) -> Question:
        """Create a new bank question and attach it to the end of a template."""
        await self._owned_template_or_404(db, template_id, user_id)

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
        await db.flush()

        db.add(
            ExamTemplateQuestion(
                exam_template_id=template_id,
                question_id=question.id,
                order_index=await self._next_order_index(db, template_id),
            )
        )
        await db.flush()
        await self._sync_total_questions(db, template_id)

        await db.commit()
        await db.refresh(question)
        return question

    async def attach_questions(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        question_ids: List[uuid.UUID],
    ) -> List[Tuple[Question, int]]:
        """Append existing bank questions to a template's composition."""
        await self._owned_template_or_404(db, template_id, user_id)

        found = (
            await db.execute(
                select(Question.id).where(
                    Question.id.in_(question_ids),
                    Question.archived_at.is_(None),
                )
            )
        ).scalars().all()
        missing = set(question_ids) - set(found)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unknown or archived question ids: {sorted(str(m) for m in missing)}",
            )

        already = set(
            (
                await db.execute(
                    select(ExamTemplateQuestion.question_id).where(
                        ExamTemplateQuestion.exam_template_id == template_id
                    )
                )
            ).scalars().all()
        )

        # Silently skip duplicates rather than 409ing: the caller is a
        # multi-select UI where re-picking an attached question is routine.
        next_index = await self._next_order_index(db, template_id)
        for question_id in question_ids:
            if question_id in already:
                continue
            db.add(
                ExamTemplateQuestion(
                    exam_template_id=template_id,
                    question_id=question_id,
                    order_index=next_index,
                )
            )
            already.add(question_id)
            next_index += 1

        await db.flush()
        await self._sync_total_questions(db, template_id)
        await db.commit()
        return await self.get_questions_with_order(db, template_id)

    async def reorder_questions(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        question_ids: List[uuid.UUID],
    ) -> List[Tuple[Question, int]]:
        """
        Rewrite order_index across a template's whole composition.

        Rejects a partial list rather than applying it — omitted questions
        would otherwise keep stale indices and interleave unpredictably.
        """
        await self._owned_template_or_404(db, template_id, user_id)

        links = list(
            (
                await db.execute(
                    select(ExamTemplateQuestion).where(
                        ExamTemplateQuestion.exam_template_id == template_id
                    )
                )
            ).scalars().all()
        )
        by_question = {link.question_id: link for link in links}
        if set(question_ids) != set(by_question) or len(question_ids) != len(links):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="questionIds must contain exactly the questions in this exam",
            )

        for index, question_id in enumerate(question_ids):
            by_question[question_id].order_index = index

        await db.commit()
        return await self.get_questions_with_order(db, template_id)

    async def detach_question(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        """Remove a question from one exam. The question itself survives."""
        await self._owned_template_or_404(db, template_id, user_id)

        link = (
            await db.execute(
                select(ExamTemplateQuestion).where(
                    ExamTemplateQuestion.exam_template_id == template_id,
                    ExamTemplateQuestion.question_id == question_id,
                )
            )
        ).scalar_one_or_none()
        if not link:
            return False

        await db.delete(link)
        await db.flush()
        await self._sync_total_questions(db, template_id)
        await db.commit()
        return True

    # ─── QUESTIONS ───────────────────────────────────────────────
    # Question CRUD lives in QuestionService; these thin wrappers keep the
    # legacy /api/exams/questions/{id} routes working against one implementation.
    async def update_question(
        self,
        db: AsyncSession,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
        req: QuestionUpdateRequest,
    ) -> Optional[Question]:
        return await question_service.update_question(db, question_id, user_id, req)

    async def delete_question(
        self,
        db: AsyncSession,
        question_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> bool:
        return await question_service.delete_question(
            db, question_id, user_id
        )

    # ─── SESSIONS ────────────────────────────────────────────────
    async def get_user_sessions(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> List[ExamSession]:
        """Fetch recent 50 exam sessions for a user."""
        stmt = (
            select(ExamSession)
            .where(ExamSession.user_id == user_id)
            .order_by(ExamSession.created_at.desc())
            .limit(50)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def create_session(
        self, db: AsyncSession, user_id: uuid.UUID, template_id: uuid.UUID
    ) -> ExamSession:
        """Start a new exam session for a template."""
        template = await self.get_template_by_id(db, template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Exam template not found"
            )

        questions = await self.get_questions(db, template_id)

        session = ExamSession(
            user_id=user_id,
            exam_template_id=template_id,
            time_limit_minutes=template.duration_minutes,
            score=0.0,
            correct_count=0,
            total_count=len(questions),
            status="in-progress",
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)

        # Pre-create one empty answer record per question. This set doubles as
        # the composition snapshot for this sitting — `order_index` freezes the
        # order so later edits to the template can't rewrite it.
        answer_records = [
            AnswerRecord(
                session_id=session.id,
                question_id=q.id,
                order_index=index,
                user_answer="",
                is_correct=False,
                time_taken_seconds=0,
            )
            for index, q in enumerate(questions)
        ]
        db.add_all(answer_records)
        await db.commit()

        return session

    async def get_session_by_id(
        self, db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[ExamSession]:
        """Fetch exam session by ID verifying ownership."""
        result = await db.execute(
            select(ExamSession).where(
                ExamSession.id == session_id, ExamSession.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_session_details(
        self, db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Fetch full session details, template metadata, questions, and user answers map."""
        session = await self.get_session_by_id(db, session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Exam session not found"
            )

        template = await self.get_template_by_id(db, session.exam_template_id)

        # Resolve the questions through this session's own answer records, NOT
        # through the template's current composition. Reading the template
        # would mean attaching/detaching/reordering an exam — or re-seeding it
        # — retroactively changed what a finished session "was". Archived
        # questions are intentionally still resolved here so past results stay
        # readable after a bank deletion.
        questions = list(
            (
                await db.execute(
                    select(Question)
                    .join(AnswerRecord, AnswerRecord.question_id == Question.id)
                    .where(AnswerRecord.session_id == session_id)
                    .order_by(AnswerRecord.order_index.asc(), Question.id.asc())
                )
            ).scalars().all()
        )

        # Fetch answer records
        ans_stmt = select(AnswerRecord).where(AnswerRecord.session_id == session_id)
        ans_res = await db.execute(ans_stmt)
        answers = ans_res.scalars().all()

        user_answers_map = {}
        for a in answers:
            user_answers_map[str(a.question_id)] = {
                "userAnswer": a.user_answer,
                "isCorrect": a.is_correct,
                "timeTakenSeconds": a.time_taken_seconds,
            }

        return {
            "session": session,
            "template": template,
            "questions": questions,
            "userAnswers": user_answers_map,
        }

    async def record_answer(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        req: SubmitAnswerRequest,
    ) -> AnswerRecord:
        """Submit or update an answer for a single question in an active exam session."""
        session = await self.get_session_by_id(db, session_id, user_id)
        if not session or session.status != "in-progress":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Active exam session not found or already completed",
            )

        # The answer record must already exist — `create_session` pre-creates
        # exactly one per question in the exam. Creating one on demand here
        # (the previous behaviour) let a client PUT answers for arbitrary
        # question ids that were never part of the session, inflating
        # `correctCount` past `totalCount` when `finish_session` summed them.
        ans_res = await db.execute(
            select(AnswerRecord).where(
                AnswerRecord.session_id == session_id,
                AnswerRecord.question_id == req.question_id,
            )
        )
        record = ans_res.scalar_one_or_none()
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question is not part of this exam session",
            )

        q_res = await db.execute(
            select(Question).where(Question.id == req.question_id)
        )
        q = q_res.scalar_one_or_none()
        if not q:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
            )

        is_correct = (
            req.user_answer.strip().upper() == q.correct_answer.strip().upper()
        )

        record.user_answer = req.user_answer
        record.is_correct = is_correct
        record.time_taken_seconds = req.time_taken_seconds

        await db.commit()
        await db.refresh(record)
        return record

    async def finish_session(
        self, db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExamSession:
        """Finalize an active exam session, calculate score percentage, and mark completed."""
        session = await self.get_session_by_id(db, session_id, user_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )

        ans_res = await db.execute(
            select(AnswerRecord).where(AnswerRecord.session_id == session_id)
        )
        answers = ans_res.scalars().all()

        correct_count = sum(1 for a in answers if a.is_correct)
        total_count = session.total_count or len(answers)
        score = (correct_count / total_count * 100.0) if total_count > 0 else 0.0

        session.status = "completed"
        session.correct_count = correct_count
        session.score = round(score, 1)
        session.finished_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(session)
        return session
