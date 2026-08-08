import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class ExamTemplateCreateRequest(BaseModel):
    name: str
    exam_type: str = Field(alias="examType")
    description: Optional[str] = None
    duration_minutes: int = Field(alias="durationMinutes")
    passing_score: int = Field(default=60, alias="passingScore")
    level: Optional[str] = None
    is_public: bool = Field(default=False, alias="isPublic")
    tags: Optional[List[str]] = None

    model_config = ConfigDict(populate_by_name=True)


class ExamTemplateResponse(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = Field(default=None, alias="userId")
    name: str
    exam_type: str = Field(alias="examType")
    description: Optional[str] = None
    duration_minutes: int = Field(alias="durationMinutes")
    total_questions: int = Field(default=0, alias="totalQuestions")
    passing_score: int = Field(default=60, alias="passingScore")
    level: Optional[str] = None
    is_public: bool = Field(default=False, alias="isPublic")
    tags: Optional[List[str]] = None
    # Derived from the template's questions, not stored: parts live on
    # questions, but the hub needs them to offer part filter chips.
    parts: List[str] = Field(default_factory=list)
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @computed_field(alias="_id")
    def mongo_id(self) -> str:
        return str(self.id)


class ExamTemplateUpdateRequest(BaseModel):
    """Full replacement of a custom template's metadata (PUT semantics)."""

    name: str
    exam_type: str = Field(alias="examType")
    description: Optional[str] = None
    duration_minutes: int = Field(alias="durationMinutes")
    passing_score: int = Field(default=60, alias="passingScore")
    level: Optional[str] = None
    tags: Optional[List[str]] = None

    model_config = ConfigDict(populate_by_name=True)


def _normalize_part(value: Optional[str]) -> Optional[str]:
    """
    Fold `"Part 5"` / `"PART5"` / `" part5 "` onto one value.

    `part` is free-form by design, so normalizing at the boundary is what keeps
    the filter chips from fragmenting into near-duplicate entries.
    """
    if value is None:
        return None
    normalized = value.strip().lower().replace(" ", "")
    return normalized or None


class QuestionCreateRequest(BaseModel):
    exam_type: str = Field(alias="examType")
    part: Optional[str] = None
    passage_group: Optional[str] = Field(default=None, alias="passageGroup")
    question_text: str = Field(alias="questionText")
    passage: Optional[str] = None
    type: str = "multiple-choice"
    options: List[str] = Field(min_length=4, max_length=4)
    correct_answer: str = Field(alias="correctAnswer")
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: str = "medium"

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("part")
    @classmethod
    def normalize_part(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_part(v)


class QuestionUpdateRequest(BaseModel):
    """Full replacement of a question's content (PUT semantics)."""

    exam_type: str = Field(alias="examType")
    part: Optional[str] = None
    passage_group: Optional[str] = Field(default=None, alias="passageGroup")
    question_text: str = Field(alias="questionText")
    passage: Optional[str] = None
    type: str = "multiple-choice"
    options: List[str] = Field(min_length=4, max_length=4)
    correct_answer: str = Field(alias="correctAnswer")
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: str = "medium"

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("part")
    @classmethod
    def normalize_part(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_part(v)


class QuestionResponsePublic(BaseModel):
    """
    A question as it exists in the bank — independent of any exam.
    This public schema omits the correct answer and explanation.
    """

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = Field(default=None, alias="userId")
    exam_type: str = Field(alias="examType")
    part: Optional[str] = None
    passage_group: Optional[str] = Field(default=None, alias="passageGroup")
    question_text: str = Field(alias="questionText")
    passage: Optional[str] = None
    type: str = "multiple-choice"
    options: List[str]
    tags: Optional[List[str]] = None
    difficulty: str = "medium"
    # Router-populated: the frontend holds only a token, never a user id, so it
    # cannot work out on its own which rows it may edit. Without this the bank
    # UI would offer edit/delete on seeded questions and get a silent 404.
    is_owned: bool = Field(default=False, alias="isOwned")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @computed_field(alias="_id")
    def mongo_id(self) -> str:
        return str(self.id)


class QuestionResponse(QuestionResponsePublic):
    """The full question schema, including answer keys, for authorized users."""

    correct_answer: str = Field(alias="correctAnswer")
    explanation: Optional[str] = None


class TemplateQuestionResponsePublic(QuestionResponsePublic):
    """A bank question plus its position within one exam template."""

    order_index: int = Field(default=0, alias="orderIndex")


class TemplateQuestionResponse(QuestionResponse):
    """A bank question plus its position within one exam template."""

    order_index: int = Field(default=0, alias="orderIndex")


def _is_owned(question: Any, current_user_id: Optional[uuid.UUID]) -> bool:
    """Seeded questions have `user_id = NULL` and are owned by nobody."""
    owner_id = getattr(question, "user_id", None)
    return bool(current_user_id) and owner_id == current_user_id


def build_question_response(
    question: Any, current_user_id: Optional[uuid.UUID]
) -> Union["QuestionResponse", "QuestionResponsePublic"]:
    """Serialize a bank question, stamping viewer-relative ownership."""
    is_owned = _is_owned(question, current_user_id)
    if is_owned:
        response = QuestionResponse.model_validate(question)
    else:
        response = QuestionResponsePublic.model_validate(question)
    response.is_owned = is_owned
    return response


def build_session_question_response(
    question: Any, reveal_keys: bool
) -> Union["QuestionResponse", "QuestionResponsePublic"]:
    """
    Serialize a question as it appears inside one exam sitting.

    Gated on the *session* (owner + completed, decided by
    `ExamService.get_session_details`), not on who authored the question:
    built-in questions have `user_id = NULL`, so reusing
    `build_question_response` here would strip the key out of every seeded
    exam's results page.
    """
    if reveal_keys:
        return QuestionResponse.model_validate(question)
    return QuestionResponsePublic.model_validate(question)


def build_template_question_response(
    question: Any, order_index: int, current_user_id: Optional[uuid.UUID]
) -> Union["TemplateQuestionResponse", "TemplateQuestionResponsePublic"]:
    """Serialize a question together with its position in one exam template."""
    is_owned = _is_owned(question, current_user_id)
    if is_owned:
        response = TemplateQuestionResponse.model_validate(question)
    else:
        response = TemplateQuestionResponsePublic.model_validate(question)
    response.order_index = order_index
    response.is_owned = is_owned
    return response


class AttachQuestionsRequest(BaseModel):
    """Existing bank questions to append to a template's composition."""

    question_ids: List[uuid.UUID] = Field(alias="questionIds")

    model_config = ConfigDict(populate_by_name=True)


class ReorderQuestionsRequest(BaseModel):
    """New order for a template's questions; must cover the composition exactly."""

    question_ids: List[uuid.UUID] = Field(alias="questionIds")

    model_config = ConfigDict(populate_by_name=True)


class ExamSessionCreateRequest(BaseModel):
    exam_template_id: uuid.UUID = Field(alias="examTemplateId")

    model_config = ConfigDict(populate_by_name=True)


class ExamSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID = Field(alias="userId")
    exam_template_id: uuid.UUID = Field(alias="examTemplateId")
    started_at: datetime = Field(alias="startedAt")
    finished_at: Optional[datetime] = Field(default=None, alias="finishedAt")
    time_limit_minutes: int = Field(alias="timeLimitMinutes")
    score: float = 0.0
    correct_count: int = Field(default=0, alias="correctCount")
    total_count: int = Field(default=0, alias="totalCount")
    status: str = "in-progress"

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @computed_field(alias="_id")
    def mongo_id(self) -> str:
        return str(self.id)


class SubmitAnswerRequest(BaseModel):
    question_id: uuid.UUID = Field(alias="questionId")
    user_answer: str = Field(alias="userAnswer")
    time_taken_seconds: int = Field(default=0, alias="timeTakenSeconds")

    model_config = ConfigDict(populate_by_name=True)


class SessionDetailsResponse(BaseModel):
    session: ExamSessionResponse
    template: ExamTemplateResponse
    # Keyed shape while reviewing a completed sitting, key-free while it is still
    # in progress — see `build_session_question_response`.
    questions: List[Union[QuestionResponse, QuestionResponsePublic]]
    user_answers: Dict[str, Any] = Field(alias="userAnswers")

    model_config = ConfigDict(populate_by_name=True)
