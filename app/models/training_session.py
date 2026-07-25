from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class TrainingType(StrEnum):
    daily = "daily"
    subject = "subject"
    wrong_review = "wrong_review"
    mixed = "mixed"


class TrainingSessionStatus(StrEnum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TrainingSession(TimestampMixin, Base):
    __tablename__ = "training_sessions"
    __table_args__ = (
        CheckConstraint("total_questions BETWEEN 1 AND 100", name="ck_training_question_count"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    training_type: Mapped[TrainingType] = mapped_column(Enum(TrainingType), index=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[TrainingSessionStatus] = mapped_column(
        Enum(TrainingSessionStatus), default=TrainingSessionStatus.pending, index=True
    )
    total_questions: Mapped[int] = mapped_column(Integer)
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    chapter: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    knowledge_point: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    plan_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    selection_version: Mapped[str] = mapped_column(String(30))
    selection_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="training_sessions")  # noqa: F821
    items: Mapped[list["TrainingSessionItem"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="TrainingSessionItem.position",
    )


class TrainingSessionItem(TimestampMixin, Base):
    __tablename__ = "training_session_items"
    __table_args__ = (
        UniqueConstraint("session_id", "position", name="uq_training_item_position"),
        UniqueConstraint("session_id", "question_id", name="uq_training_item_question"),
        CheckConstraint("position >= 1", name="ck_training_item_position"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("training_sessions.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    recommendation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_answer_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "student_answers.id",
            name="training_session_items_source_answer_id_fkey",
            ondelete="SET NULL",
            use_alter=True,
        ),
        nullable=True,
        index=True,
    )

    session: Mapped[TrainingSession] = relationship(back_populates="items")
    question: Mapped["Question"] = relationship(back_populates="training_session_items")  # noqa: F821
    answer: Mapped["StudentAnswer | None"] = relationship(  # noqa: F821
        back_populates="training_session_item",
        foreign_keys="StudentAnswer.training_session_item_id",
        uselist=False,
    )
