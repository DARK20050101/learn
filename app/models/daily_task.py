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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class DailyTaskStatus(StrEnum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"


class DailyTask(TimestampMixin, Base):
    __tablename__ = "daily_tasks"
    __table_args__ = (
        UniqueConstraint("user_id", "task_date", name="uq_daily_task_user_date"),
        CheckConstraint("version BETWEEN 1 AND 2", name="ck_daily_task_version"),
        CheckConstraint("refresh_count BETWEEN 0 AND 1", name="ck_daily_task_refresh_count"),
        CheckConstraint("version = refresh_count + 1", name="ck_daily_task_refresh_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_date: Mapped[date] = mapped_column(Date, index=True)
    day_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[DailyTaskStatus] = mapped_column(
        Enum(DailyTaskStatus), default=DailyTaskStatus.pending, index=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    recommendation_version: Mapped[str] = mapped_column(String(30), default="rules-v1")
    version: Mapped[int] = mapped_column(Integer, default=1)
    refresh_count: Mapped[int] = mapped_column(Integer, default=0)
    refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="daily_tasks")  # noqa: F821
    items: Mapped[list["DailyTaskItem"]] = relationship(
        back_populates="task", cascade="all, delete-orphan", order_by="DailyTaskItem.position"
    )  # noqa: F821


class DailyTaskItem(TimestampMixin, Base):
    __tablename__ = "daily_task_items"
    __table_args__ = (
        UniqueConstraint("daily_task_id", "position", name="uq_task_item_position"),
        UniqueConstraint("daily_task_id", "question_id", name="uq_task_item_question"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    daily_task_id: Mapped[int] = mapped_column(
        ForeignKey("daily_tasks.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="RESTRICT"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    recommendation_reason: Mapped[str | None] = mapped_column(String(255))

    task: Mapped[DailyTask] = relationship(back_populates="items")
    question: Mapped["Question"] = relationship(back_populates="task_items")  # noqa: F821
    answers: Mapped[list["StudentAnswer"]] = relationship(back_populates="daily_task_item")  # noqa: F821
