from enum import StrEnum

from sqlalchemy import Boolean, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class QuestionType(StrEnum):
    single_choice = "single_choice"
    multiple_choice = "multiple_choice"
    true_false = "true_false"
    short_answer = "short_answer"
    fill_blank = "fill_blank"


class Question(TimestampMixin, Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    content: Mapped[str] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(String(50), index=True)
    chapter: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    question_type: Mapped[QuestionType] = mapped_column(Enum(QuestionType), index=True)
    options: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    correct_answer: Mapped[str | list[str] | bool] = mapped_column(JSONB)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, index=True)
    knowledge_points: Mapped[list[str]] = mapped_column(JSONB, default=list)
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    student_answers: Mapped[list["StudentAnswer"]] = relationship(  # noqa: F821
        back_populates="question", cascade="all, delete-orphan"
    )
    task_items: Mapped[list["DailyTaskItem"]] = relationship(back_populates="question")  # noqa: F821
    training_session_items: Mapped[list["TrainingSessionItem"]] = relationship(  # noqa: F821
        back_populates="question"
    )
    knowledge_point_links: Mapped[list["QuestionKnowledgePoint"]] = relationship(  # noqa: F821
        back_populates="question",
        cascade="all, delete-orphan",
    )
