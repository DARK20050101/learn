from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class KnowledgePoint(TimestampMixin, Base):
    __tablename__ = "knowledge_points"
    __table_args__ = (
        CheckConstraint("level BETWEEN 1 AND 3", name="ck_knowledge_point_level"),
        UniqueConstraint("code", name="uq_knowledge_points_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(100))
    subject: Mapped[str] = mapped_column(String(50), index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("knowledge_points.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    grade_scope: Mapped[str | None] = mapped_column(String(30), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    parent: Mapped["KnowledgePoint | None"] = relationship(
        remote_side="KnowledgePoint.id",
        back_populates="children",
    )
    children: Mapped[list["KnowledgePoint"]] = relationship(back_populates="parent")
    aliases: Mapped[list["KnowledgePointAlias"]] = relationship(
        back_populates="knowledge_point",
        cascade="all, delete-orphan",
    )
    question_links: Mapped[list["QuestionKnowledgePoint"]] = relationship(
        back_populates="knowledge_point"
    )
    statuses: Mapped[list["KnowledgeStatus"]] = relationship(  # noqa: F821
        back_populates="standard_knowledge_point"
    )


class KnowledgePointAlias(TimestampMixin, Base):
    __tablename__ = "knowledge_point_aliases"
    __table_args__ = (
        UniqueConstraint(
            "subject",
            "normalized_alias",
            name="uq_knowledge_point_alias_subject_normalized",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    knowledge_point_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_points.id", ondelete="CASCADE"),
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(50), index=True)
    alias: Mapped[str] = mapped_column(String(100))
    normalized_alias: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    knowledge_point: Mapped[KnowledgePoint] = relationship(back_populates="aliases")


class QuestionKnowledgePoint(TimestampMixin, Base):
    __tablename__ = "question_knowledge_points"
    __table_args__ = (
        UniqueConstraint(
            "question_id",
            "knowledge_point_id",
            name="uq_question_knowledge_point",
        ),
        CheckConstraint(
            "role IN ('primary', 'secondary')",
            name="ck_question_knowledge_point_role",
        ),
        CheckConstraint(
            "weight > 0 AND weight <= 1",
            name="ck_question_knowledge_point_weight",
        ),
        Index(
            "uq_question_primary_knowledge_point",
            "question_id",
            unique=True,
            postgresql_where=text("role = 'primary'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"),
        index=True,
    )
    knowledge_point_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_points.id", ondelete="RESTRICT"),
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20))
    weight: Mapped[float] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(30), nullable=True)
    mapping_version: Mapped[str | None] = mapped_column(String(30), nullable=True)

    question: Mapped["Question"] = relationship(back_populates="knowledge_point_links")  # noqa: F821
    knowledge_point: Mapped[KnowledgePoint] = relationship(back_populates="question_links")


class KnowledgeStatusMigrationBackup(TimestampMixin, Base):
    __tablename__ = "knowledge_status_migration_backups"
    __table_args__ = (
        UniqueConstraint(
            "migration_batch",
            "original_status_id",
            name="uq_knowledge_status_backup_batch_original",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    migration_batch: Mapped[str] = mapped_column(String(50), index=True)
    original_status_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True)
    knowledge_point: Mapped[str | None] = mapped_column(String(100), nullable=True)
    attempt_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    correct_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_gap_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mastery_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_practiced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    target_knowledge_point_id: Mapped[int | None] = mapped_column(
        ForeignKey("knowledge_points.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    mapping_version: Mapped[str | None] = mapped_column(String(30), nullable=True)
    merge_target_status_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    backup_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
