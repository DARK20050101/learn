from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    student_answers: Mapped[list["StudentAnswer"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    daily_tasks: Mapped[list["DailyTask"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    knowledge_statuses: Mapped[list["KnowledgeStatus"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
    training_sessions: Mapped[list["TrainingSession"]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
