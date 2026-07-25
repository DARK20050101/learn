from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class KnowledgeStatus(TimestampMixin, Base):
    __tablename__ = "knowledge_status"
    __table_args__ = (
        UniqueConstraint("user_id", "subject", "knowledge_point", name="uq_user_knowledge_point"),
        CheckConstraint(
            "mastery_score >= 0 AND mastery_score <= 100", name="ck_mastery_score_range"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject: Mapped[str] = mapped_column(String(50), index=True)
    knowledge_point: Mapped[str] = mapped_column(String(100), index=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    ai_gap_count: Mapped[int] = mapped_column(Integer, default=0)
    mastery_score: Mapped[float] = mapped_column(Float, default=0)
    last_practiced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    knowledge_point_id: Mapped[int | None] = mapped_column(
        ForeignKey("knowledge_points.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    mapping_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    mapped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="knowledge_statuses")  # noqa: F821
    standard_knowledge_point: Mapped["KnowledgePoint | None"] = relationship(  # noqa: F821
        back_populates="statuses"
    )
