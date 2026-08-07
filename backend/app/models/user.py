import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.deck import Deck
    from app.models.card import Card
    from app.models.exam import ExamTemplate
    from app.models.session import ExamSession
    from app.models.settings import UserSettings


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    google_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True, nullable=True)
    is_guest: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    daily_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Indexed because the guest cleanup job sweeps on (is_guest, last_active).
    last_active: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    # Audit/abuse metadata only — never an identity key. Guests are identified by
    # their token, since NAT puts unrelated people behind a single address.
    # 45 chars covers IPv6, including the IPv4-mapped ::ffff:255.255.255.255 form.
    last_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
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
    decks: Mapped[List["Deck"]] = relationship("Deck", back_populates="user", cascade="all, delete-orphan")
    cards: Mapped[List["Card"]] = relationship("Card", back_populates="user", cascade="all, delete-orphan")
    exam_templates: Mapped[List["ExamTemplate"]] = relationship("ExamTemplate", back_populates="user")
    exam_sessions: Mapped[List["ExamSession"]] = relationship("ExamSession", back_populates="user", cascade="all, delete-orphan")
    user_settings: Mapped[Optional["UserSettings"]] = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
