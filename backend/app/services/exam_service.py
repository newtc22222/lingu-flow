import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import ExamTemplate, Question
from app.models.session import AnswerRecord, ExamSession
from app.schemas.exam import (
    ExamSessionCreateRequest,
    ExamTemplateCreateRequest,
    QuestionCreateRequest,
    SubmitAnswerRequest,
)


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

    # ─── QUESTIONS ───────────────────────────────────────────────
    async def get_questions(
        self, db: AsyncSession, template_id: uuid.UUID
    ) -> List[Question]:
        """Fetch all questions for a template ordered by order_index."""
        stmt = (
            select(Question)
            .where(Question.exam_template_id == template_id)
            .order_by(Question.order_index.asc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def add_question(
        self,
        db: AsyncSession,
        template_id: uuid.UUID,
        user_id: uuid.UUID,
        req: QuestionCreateRequest,
    ) -> Question:
        """Add a question to a template."""
        template = await self.get_template_by_id(db, template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
            )

        question = Question(
            exam_template_id=template_id,
            user_id=user_id,
            question_text=req.question_text,
            passage=req.passage,
            type=req.type,
            options=req.options,
            correct_answer=req.correct_answer,
            explanation=req.explanation,
            tags=req.tags or [],
            difficulty=req.difficulty,
            order_index=req.order_index,
        )
        db.add(question)

        # Update total questions count on template
        template.total_questions += 1
        await db.commit()
        await db.refresh(question)
        return question

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

        # Pre-create empty answer records for questions
        answer_records = [
            AnswerRecord(
                session_id=session.id,
                question_id=q.id,
                user_answer="",
                is_correct=False,
                time_taken_seconds=0,
            )
            for q in questions
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
        questions = await self.get_questions(db, session.exam_template_id)

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

        # Fetch question to check correct answer
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

        # Find existing AnswerRecord or create new
        ans_res = await db.execute(
            select(AnswerRecord).where(
                AnswerRecord.session_id == session_id,
                AnswerRecord.question_id == req.question_id,
            )
        )
        record = ans_res.scalar_one_or_none()

        if not record:
            record = AnswerRecord(
                session_id=session_id,
                question_id=req.question_id,
                user_answer=req.user_answer,
                is_correct=is_correct,
                time_taken_seconds=req.time_taken_seconds,
            )
            db.add(record)
        else:
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
