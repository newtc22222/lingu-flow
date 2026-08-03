import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_optional_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.exam import (
    ExamSessionCreateRequest,
    ExamSessionResponse,
    ExamTemplateCreateRequest,
    ExamTemplateResponse,
    QuestionCreateRequest,
    QuestionResponse,
    SessionDetailsResponse,
    SubmitAnswerRequest,
)
from app.services.exam_service import ExamService

router = APIRouter(prefix="/api/exams", tags=["Exam Simulator"])
exam_service = ExamService()


# ─── TEMPLATES ───────────────────────────────────────────────────
@router.get("/templates", response_model=List[ExamTemplateResponse])
async def get_templates(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List public exam templates plus custom templates owned by user."""
    user_id = current_user.id if current_user else None
    templates = await exam_service.get_templates(db, user_id)
    return [ExamTemplateResponse.model_validate(t) for t in templates]


@router.post(
    "/templates",
    response_model=ExamTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    req: ExamTemplateCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom exam template."""
    template = await exam_service.create_template(db, current_user.id, req)
    return ExamTemplateResponse.model_validate(template)


@router.get("/templates/{template_id}", response_model=ExamTemplateResponse)
async def get_template_by_id(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get exam template metadata by ID."""
    template = await exam_service.get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return ExamTemplateResponse.model_validate(template)


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a custom template owned by user."""
    success = await exam_service.delete_template(db, template_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom template not found or cannot delete public template",
        )
    return {"success": True}


# ─── QUESTIONS ───────────────────────────────────────────────────
@router.get(
    "/templates/{template_id}/questions", response_model=List[QuestionResponse]
)
async def get_template_questions(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Fetch all questions for a template ordered by index."""
    questions = await exam_service.get_questions(db, template_id)
    return [QuestionResponse.model_validate(q) for q in questions]


@router.post(
    "/templates/{template_id}/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_template_question(
    template_id: uuid.UUID,
    req: QuestionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a question to a template."""
    question = await exam_service.add_question(
        db, template_id, current_user.id, req
    )
    return QuestionResponse.model_validate(question)


# ─── SESSIONS ────────────────────────────────────────────────────
@router.get("/sessions", response_model=List[ExamSessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch recent exam history for current user."""
    sessions = await exam_service.get_user_sessions(db, current_user.id)
    return [ExamSessionResponse.model_validate(s) for s in sessions]


@router.post(
    "/sessions",
    response_model=ExamSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def start_session(
    req: ExamSessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a new exam session for a template."""
    session = await exam_service.create_session(
        db, current_user.id, req.exam_template_id
    )
    return ExamSessionResponse.model_validate(session)


@router.get("/sessions/{session_id}", response_model=ExamSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get exam session status by ID."""
    session = await exam_service.get_session_by_id(db, session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
        )
    return ExamSessionResponse.model_validate(session)


@router.get("/sessions/{session_id}/details", response_model=SessionDetailsResponse)
async def get_session_details(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete session details, template metadata, questions, and user answers map."""
    details = await exam_service.get_session_details(db, session_id, current_user.id)
    return SessionDetailsResponse(
        session=ExamSessionResponse.model_validate(details["session"]),
        template=ExamTemplateResponse.model_validate(details["template"]),
        questions=[QuestionResponse.model_validate(q) for q in details["questions"]],
        user_answers=details["userAnswers"],
    )


@router.put("/sessions/{session_id}/answer")
async def record_answer(
    session_id: uuid.UUID,
    req: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Record or update an answer for a single question in an active exam session."""
    record = await exam_service.record_answer(
        db, session_id, current_user.id, req
    )
    return {
        "success": True,
        "questionId": str(record.question_id),
        "userAnswer": record.user_answer,
        "isCorrect": record.is_correct,
    }


@router.put("/sessions/{session_id}/finish", response_model=ExamSessionResponse)
async def finish_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Finalize an active exam session, calculate score, and set status to completed."""
    session = await exam_service.finish_session(db, session_id, current_user.id)
    return ExamSessionResponse.model_validate(session)
