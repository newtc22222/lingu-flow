import uuid
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_optional_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.exam import (
    AttachQuestionsRequest,
    ExamSessionCreateRequest,
    ExamSessionResponse,
    ExamTemplateCreateRequest,
    ExamTemplateResponse,
    ExamTemplateUpdateRequest,
    QuestionCreateRequest,
    QuestionResponse,
    QuestionUpdateRequest,
    ReorderQuestionsRequest,
    SessionDetailsResponse,
    SubmitAnswerRequest,
    TemplateQuestionResponse,
    TemplateQuestionResponsePublic,
    build_question_response,
    build_session_question_response,
    build_template_question_response,
)
from app.services.exam_service import ExamService

router = APIRouter(prefix="/api/exams", tags=["Exam Simulator"])
exam_service = ExamService()


def viewer_id(current_user: Optional[User]) -> Optional[uuid.UUID]:
    """Id of whoever is asking, or None when unauthenticated — drives `isOwned`."""
    return current_user.id if current_user else None


# ─── TEMPLATES ───────────────────────────────────────────────────
@router.get("/templates", response_model=List[ExamTemplateResponse])
async def get_templates(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List public exam templates plus custom templates owned by user."""
    user_id = current_user.id if current_user else None
    templates = await exam_service.get_templates(db, user_id)
    parts_by_template = await exam_service.get_parts_by_template(
        db, [t.id for t in templates]
    )

    responses = []
    for template in templates:
        response = ExamTemplateResponse.model_validate(template)
        response.parts = parts_by_template.get(template.id, [])
        responses.append(response)
    return responses


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
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get exam template metadata by ID, if the viewer may read it."""
    template = await exam_service.readable_template_or_404(
        db, template_id, viewer_id(current_user)
    )
    return ExamTemplateResponse.model_validate(template)


@router.put("/templates/{template_id}", response_model=ExamTemplateResponse)
async def update_template(
    template_id: uuid.UUID,
    req: ExamTemplateUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a custom exam template owned by the user."""
    template = await exam_service.update_template(
        db, template_id, current_user.id, req
    )
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Custom template not found or cannot edit public template",
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
    "/templates/{template_id}/questions",
    response_model=List[Union[TemplateQuestionResponse, TemplateQuestionResponsePublic]],
)
async def get_template_questions(
    template_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a template's questions in composition order, if the viewer may read it."""
    await exam_service.readable_template_or_404(
        db, template_id, viewer_id(current_user)
    )
    pairs = await exam_service.get_questions_with_order(db, template_id)
    return [
        build_template_question_response(q, order_index, viewer_id(current_user))
        for q, order_index in pairs
    ]


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
    """Create a new bank question and attach it to the end of this template."""
    question = await exam_service.add_question(
        db, template_id, current_user.id, req
    )
    return build_question_response(question, viewer_id(current_user))


@router.post(
    "/templates/{template_id}/questions/attach",
    response_model=List[Union[TemplateQuestionResponse, TemplateQuestionResponsePublic]],
)
async def attach_template_questions(
    template_id: uuid.UUID,
    req: AttachQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Append existing bank questions to this template's composition."""
    pairs = await exam_service.attach_questions(
        db, template_id, current_user.id, req.question_ids
    )
    return [
        build_template_question_response(q, order_index, viewer_id(current_user))
        for q, order_index in pairs
    ]


@router.put(
    "/templates/{template_id}/questions/reorder",
    response_model=List[Union[TemplateQuestionResponse, TemplateQuestionResponsePublic]],
)
async def reorder_template_questions(
    template_id: uuid.UUID,
    req: ReorderQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rewrite the order of this template's questions. Must cover them exactly."""
    pairs = await exam_service.reorder_questions(
        db, template_id, current_user.id, req.question_ids
    )
    return [
        build_template_question_response(q, order_index, viewer_id(current_user))
        for q, order_index in pairs
    ]


@router.delete("/templates/{template_id}/questions/{question_id}")
async def detach_template_question(
    template_id: uuid.UUID,
    question_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a question from this exam. It survives in the question bank."""
    success = await exam_service.detach_question(
        db, template_id, question_id, current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question is not part of this exam",
        )
    return {"success": True}


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: uuid.UUID,
    req: QuestionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a single question owned by the user."""
    question = await exam_service.update_question(
        db, question_id, current_user.id, req
    )
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found or not authorized",
        )
    return build_question_response(question, viewer_id(current_user))


@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive a question owned by the user (see `delete_question` for why)."""
    success = await exam_service.delete_question(
        db, question_id, current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found or not authorized",
        )
    return {"success": True}


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
    """
    Get complete session details, template metadata, questions, and user answers map.

    Owner-only (the service 404s otherwise), and answer keys are included only
    once the sitting is completed.
    """
    details = await exam_service.get_session_details(db, session_id, current_user.id)
    return SessionDetailsResponse(
        session=ExamSessionResponse.model_validate(details["session"]),
        template=ExamTemplateResponse.model_validate(details["template"]),
        questions=[
            build_session_question_response(q, details["revealAnswerKeys"])
            for q in details["questions"]
        ],
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
