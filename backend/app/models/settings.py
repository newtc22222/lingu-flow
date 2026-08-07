import uuid
from sqlalchemy import ForeignKey, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from app.database import Base


class UserSettings(Base):
    """
    Per-user settings stored as a metadata JSON column.

    The ``metadata`` column stores a freeform dict.  Known keys:
    - ``locale``            – "vi" | "en"
    - ``crtEnabled``        – bool
    - ``dailyXpGoal``       – int (target XP per day)
    - ``audioSfxEnabled``   – bool (feature flag, currently always false)
    - ``notificationsEnabled`` – bool (feature flag, currently always false)
    """
    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    settings: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="user_settings")
