import uuid
from typing import List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_optional_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.exam import (
    QuestionCreateRequest,
    QuestionResponse,
    QuestionResponsePublic,
    QuestionUpdateRequest,
    build_question_response,
)
from app.services.question_service import QuestionService

router = APIRouter(prefix="/api/questions", tags=["Question Bank"])
question_service = QuestionService()


def viewer_id(current_user: Optional[User]) -> Optional[uuid.UUID]:
    """Id of whoever is asking, or None when unauthenticated — drives `isOwned`."""
    return current_user.id if current_user else None


# NOTE: /tags and /parts MUST stay above /{question_id}. FastAPI matches routes
# in declaration order, so declaring them after would make "tags" parse as a
# UUID path param and 422.
@router.get("/tags", response_model=List[str])
async def list_tags(
    examType: Optional[str] = Query(default=None),
    part: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Distinct tags in the live bank, for filter autocomplete."""
    return await question_service.list_tags(db, exam_type=examType, part=part)


@router.get("/parts", response_model=List[str])
async def list_parts(
    examType: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Distinct non-null parts in the live bank."""
    return await question_service.list_parts(db, exam_type=examType)


@router.get("", response_model=List[Union[QuestionResponse, QuestionResponsePublic]])
async def list_questions(
    examType: Optional[str] = Query(default=None),
    part: Optional[str] = Query(default=None),
    tags: Optional[List[str]] = Query(default=None),
    difficulty: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Browse and filter the question bank."""
    questions = await question_service.list_questions(
        db,
        exam_type=examType,
        part=part,
        tags=tags,
        difficulty=difficulty,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [build_question_response(q, viewer_id(current_user)) for q in questions]


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_question(
    req: QuestionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a standalone bank question, attached to no exam."""
    question = await question_service.create_question(db, current_user.id, req)
    return build_question_response(question, viewer_id(current_user))


@router.get("/{question_id}", response_model=Union[QuestionResponse, QuestionResponsePublic])
async def get_question(
    question_id: uuid.UUID,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: AsyncSession = Depends(get_db),
):
    question = await question_service.get_question(db, question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Question not found"
        )
    return build_question_response(question, viewer_id(current_user))


@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: uuid.UUID,
    req: QuestionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a question the user owns. 409 if it changes an answered key."""
    question = await question_service.update_question(
        db, question_id, current_user.id, req
    )
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found or not authorized",
        )
    return build_question_response(question, viewer_id(current_user))


@router.delete("/{question_id}")
async def delete_question(
    question_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Archive a question the user owns, detaching it from every exam."""
    success = await question_service.delete_question(
        db, question_id, current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found or not authorized",
        )
    return {"success": True}
