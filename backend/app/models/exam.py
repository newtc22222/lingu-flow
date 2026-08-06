import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.session import ExamSession


class ExamTemplate(Base):
    __tablename__ = "exam_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    exam_type: Mapped[str] = mapped_column(String, index=True, nullable=False)  # toeic, ielts, hsk, jlpt, custom
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=60, nullable=False)  # percent
    level: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, default=list, nullable=True)

    # Built-in (seeded) templates only. `seed_key` is the stable identity the
    # seeder matches on — matching by `name` meant a content rewrite under the
    # same name silently no-op'd, and a rename orphaned the old template.
    # `seed_version` is bumped when the seed content changes.
    seed_key: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    seed_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="exam_templates")

    # The writable side of the composition. Deleting a template cascades to the
    # link rows ONLY — the questions themselves survive in the bank.
    question_links: Mapped[List["ExamTemplateQuestion"]] = relationship(
        "ExamTemplateQuestion",
        back_populates="exam_template",
        cascade="all, delete-orphan",
        order_by="ExamTemplateQuestion.order_index",
    )

    # Read-only convenience view of the same composition.
    # `viewonly=True` is required, not cosmetic: without it two relationships
    # write the same table and SQLAlchemy warns about overlapping writes.
    # Never add a delete cascade here — it would delete Question rows, which is
    # precisely the coupling this junction table exists to remove.
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        secondary="exam_template_questions",
        order_by="ExamTemplateQuestion.order_index",
        viewonly=True,
    )

    sessions: Mapped[List["ExamSession"]] = relationship("ExamSession", back_populates="exam_template", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    # Bank taxonomy. `exam_type` is required so every question is browsable;
    # `part` is free-form and nullable (TOEIC has part5/6/7, other exams may
    # gain their own). Deliberately NOT validated against the exam_type of any
    # template it's attached to — a TOEIC question in a custom mixed exam is
    # legitimate.
    exam_type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    part: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    # Groups questions that share one passage (TOEIC Parts 6/7, IELTS reading).
    # A flat marker rather than a passages table — see the follow-up issue.
    passage_group: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    # Soft delete. Bank listings filter this out; session/results resolution
    # does not, so a deleted question still renders in past results instead of
    # cascading away the answer history that references it.
    archived_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), index=True, nullable=True
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    passage: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String, default="multiple-choice", nullable=False)
    options: Mapped[dict] = mapped_column(JSON, nullable=False)  # list of 4 options
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)  # "A" | "B" | "C" | "D"
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, default=list, nullable=True)
    difficulty: Mapped[str] = mapped_column(String, default="medium", nullable=False)  # easy, medium, hard

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    template_links: Mapped[List["ExamTemplateQuestion"]] = relationship(
        "ExamTemplateQuestion",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    user: Mapped[Optional["User"]] = relationship("User")


class ExamTemplateQuestion(Base):
    """
    Join row placing a bank `Question` at a position within an `ExamTemplate`.

    This is what decouples the two: a question can appear in many templates,
    and deleting a template removes only its link rows.
    """

    __tablename__ = "exam_template_questions"
    __table_args__ = (
        # Named explicitly: Base.metadata has no naming_convention, so this
        # must match the migration byte-for-byte or autogenerate will churn.
        UniqueConstraint(
            "exam_template_id",
            "question_id",
            name="uq_exam_template_questions_template_question",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    exam_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_templates.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    exam_template: Mapped["ExamTemplate"] = relationship(
        "ExamTemplate", back_populates="question_links"
    )
    question: Mapped["Question"] = relationship(
        "Question", back_populates="template_links"
    )
