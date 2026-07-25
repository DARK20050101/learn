from enum import StrEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class AnalysisStatus(StrEnum):
    not_requested = "not_requested"
    pending = "pending"
    completed = "completed"
    failed = "failed"


class DifficultyFeedback(StrEnum):
    easy = "easy"
    difficult = "difficult"
    dont_know = "dont_know"


class StudentAnswer(TimestampMixin, Base):
    __tablename__ = "student_answers"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_answer_user_idempotency"),
        UniqueConstraint("training_session_item_id", name="uq_answer_training_session_item"),
        Index("ix_student_answers_user_created", "user_id", "created_at"),
        CheckConstraint(
            "NOT (daily_task_item_id IS NOT NULL AND training_session_item_id IS NOT NULL)",
            name="ck_answer_single_training_context",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"), index=True
    )
    daily_task_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("daily_task_items.id", ondelete="SET NULL"), index=True
    )
    training_session_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("training_session_items.id", ondelete="SET NULL"), index=True
    )
    submitted_answer: Mapped[str | list[str] | bool] = mapped_column(JSONB)
    is_correct: Mapped[bool] = mapped_column(Boolean, index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    idempotency_key: Mapped[str | None] = mapped_column(String(64))
    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus), default=AnalysisStatus.not_requested
    )
    ai_analysis: Mapped[dict | None] = mapped_column(JSONB)
    difficulty_feedback: Mapped[DifficultyFeedback | None] = mapped_column(
        Enum(DifficultyFeedback), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="student_answers")  # noqa: F821
    question: Mapped["Question"] = relationship(back_populates="student_answers")  # noqa: F821
    daily_task_item: Mapped["DailyTaskItem | None"] = relationship(back_populates="answers")  # noqa: F821
    training_session_item: Mapped["TrainingSessionItem | None"] = relationship(  # noqa: F821
        back_populates="answer",
        foreign_keys=[training_session_item_id],
    )
