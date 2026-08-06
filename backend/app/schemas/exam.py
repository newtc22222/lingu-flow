import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field


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


class QuestionCreateRequest(BaseModel):
    question_text: str = Field(alias="questionText")
    passage: Optional[str] = None
    type: str = "multiple-choice"
    options: List[str]
    correct_answer: str = Field(alias="correctAnswer")
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: str = "medium"
    order_index: int = Field(default=0, alias="orderIndex")

    model_config = ConfigDict(populate_by_name=True)


class QuestionUpdateRequest(BaseModel):
    """Full replacement of a question's content (PUT semantics)."""

    question_text: str = Field(alias="questionText")
    passage: Optional[str] = None
    type: str = "multiple-choice"
    options: List[str]
    correct_answer: str = Field(alias="correctAnswer")
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: str = "medium"

    model_config = ConfigDict(populate_by_name=True)


class QuestionResponse(BaseModel):
    id: uuid.UUID
    exam_template_id: uuid.UUID = Field(alias="examTemplateId")
    user_id: Optional[uuid.UUID] = Field(default=None, alias="userId")
    question_text: str = Field(alias="questionText")
    passage: Optional[str] = None
    type: str = "multiple-choice"
    options: List[str]
    correct_answer: str = Field(alias="correctAnswer")
    explanation: Optional[str] = None
    tags: Optional[List[str]] = None
    difficulty: str = "medium"
    order_index: int = Field(default=0, alias="orderIndex")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @computed_field(alias="_id")
    def mongo_id(self) -> str:
        return str(self.id)


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
    questions: List[QuestionResponse]
    user_answers: Dict[str, Any] = Field(alias="userAnswers")

    model_config = ConfigDict(populate_by_name=True)
