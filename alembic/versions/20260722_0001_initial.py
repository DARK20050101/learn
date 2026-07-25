"""Initial PostgreSQL schema."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260722_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    question_type = sa.Enum(
        "single_choice", "multiple_choice", "true_false", "short_answer", name="questiontype"
    )
    task_status = sa.Enum("pending", "in_progress", "completed", name="dailytaskstatus")
    analysis_status = sa.Enum(
        "not_requested", "pending", "completed", "failed", name="analysisstatus"
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table(
        "questions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("subject", sa.String(50), nullable=False),
        sa.Column("question_type", question_type, nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=True),
        sa.Column("correct_answer", postgresql.JSONB(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("difficulty", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("knowledge_points", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.CheckConstraint("difficulty BETWEEN 1 AND 5", name="ck_question_difficulty"),
    )
    for column in ("title", "subject", "question_type", "difficulty", "is_active"):
        op.create_index(f"ix_questions_{column}", "questions", [column])
    op.create_table(
        "daily_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("task_date", sa.Date(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("status", task_status, nullable=False, server_default="pending"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "recommendation_version", sa.String(30), nullable=False, server_default="rules-v1"
        ),
        *timestamps(),
        sa.UniqueConstraint("user_id", "task_date", name="uq_daily_task_user_date"),
        sa.CheckConstraint("day_number BETWEEN 1 AND 27", name="ck_daily_task_day"),
    )
    op.create_index("ix_daily_tasks_user_id", "daily_tasks", ["user_id"])
    op.create_index("ix_daily_tasks_task_date", "daily_tasks", ["task_date"])
    op.create_index("ix_daily_tasks_status", "daily_tasks", ["status"])
    op.create_table(
        "daily_task_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "daily_task_id",
            sa.Integer(),
            sa.ForeignKey("daily_tasks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("questions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("recommendation_reason", sa.String(255), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("daily_task_id", "position", name="uq_task_item_position"),
        sa.CheckConstraint("position BETWEEN 1 AND 6", name="ck_task_item_position"),
    )
    op.create_index("ix_daily_task_items_daily_task_id", "daily_task_items", ["daily_task_id"])
    op.create_index("ix_daily_task_items_question_id", "daily_task_items", ["question_id"])
    op.create_table(
        "student_answers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("questions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "daily_task_item_id",
            sa.Integer(),
            sa.ForeignKey("daily_task_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submitted_answer", postgresql.JSONB(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.String(64), nullable=True),
        sa.Column(
            "analysis_status", analysis_status, nullable=False, server_default="not_requested"
        ),
        sa.Column("ai_analysis", postgresql.JSONB(), nullable=True),
        *timestamps(),
        sa.UniqueConstraint("user_id", "idempotency_key", name="uq_answer_user_idempotency"),
    )
    for column in ("user_id", "question_id", "daily_task_item_id", "is_correct"):
        op.create_index(f"ix_student_answers_{column}", "student_answers", [column])
    op.create_index("ix_student_answers_user_created", "student_answers", ["user_id", "created_at"])
    op.create_table(
        "knowledge_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("subject", sa.String(50), nullable=False),
        sa.Column("knowledge_point", sa.String(100), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mastery_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("last_practiced_at", sa.DateTime(timezone=True), nullable=True),
        *timestamps(),
        sa.UniqueConstraint(
            "user_id", "subject", "knowledge_point", name="uq_user_knowledge_point"
        ),
        sa.CheckConstraint("mastery_score BETWEEN 0 AND 100", name="ck_mastery_score_range"),
    )
    for column in ("user_id", "subject", "knowledge_point"):
        op.create_index(f"ix_knowledge_status_{column}", "knowledge_status", [column])


def downgrade() -> None:
    op.drop_table("knowledge_status")
    op.drop_table("student_answers")
    op.drop_table("daily_task_items")
    op.drop_table("daily_tasks")
    op.drop_table("questions")
    op.drop_table("users")
    for enum_name in ("analysisstatus", "dailytaskstatus", "questiontype"):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
