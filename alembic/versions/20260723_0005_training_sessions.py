"""Add the unified training session foundation."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260723_0005"
down_revision: str | None = "20260722_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    training_type = postgresql.ENUM(
        "daily", "subject", "wrong_review", "mixed", name="trainingtype"
    )
    session_status = postgresql.ENUM(
        "pending",
        "in_progress",
        "completed",
        "cancelled",
        name="trainingsessionstatus",
    )
    training_type.create(op.get_bind(), checkfirst=True)
    session_status.create(op.get_bind(), checkfirst=True)
    training_type_column = postgresql.ENUM(
        "daily",
        "subject",
        "wrong_review",
        "mixed",
        name="trainingtype",
        create_type=False,
    )
    session_status_column = postgresql.ENUM(
        "pending",
        "in_progress",
        "completed",
        "cancelled",
        name="trainingsessionstatus",
        create_type=False,
    )

    op.create_table(
        "training_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("training_type", training_type_column, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("status", session_status_column, nullable=False, server_default="pending"),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(50), nullable=True),
        sa.Column("chapter", sa.String(100), nullable=True),
        sa.Column("knowledge_point", sa.String(100), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column("plan_day", sa.Integer(), nullable=True),
        sa.Column("selection_version", sa.String(30), nullable=False),
        sa.Column(
            "selection_config",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "total_questions BETWEEN 1 AND 100", name="ck_training_question_count"
        ),
    )
    for column in (
        "user_id",
        "training_type",
        "status",
        "subject",
        "chapter",
        "knowledge_point",
        "scheduled_date",
    ):
        op.create_index(f"ix_training_sessions_{column}", "training_sessions", [column])

    op.create_table(
        "training_session_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            sa.Integer(),
            sa.ForeignKey("training_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("questions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("recommendation_reason", sa.String(500), nullable=True),
        sa.Column(
            "source_answer_id",
            sa.Integer(),
            sa.ForeignKey("student_answers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("session_id", "position", name="uq_training_item_position"),
        sa.UniqueConstraint("session_id", "question_id", name="uq_training_item_question"),
        sa.CheckConstraint("position >= 1", name="ck_training_item_position"),
    )
    for column in ("session_id", "question_id", "source_answer_id"):
        op.create_index(
            f"ix_training_session_items_{column}", "training_session_items", [column]
        )

    op.add_column(
        "student_answers",
        sa.Column("training_session_item_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_student_answers_training_session_item",
        "student_answers",
        "training_session_items",
        ["training_session_item_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_student_answers_training_session_item_id",
        "student_answers",
        ["training_session_item_id"],
    )
    op.create_unique_constraint(
        "uq_answer_training_session_item",
        "student_answers",
        ["training_session_item_id"],
    )
    op.create_check_constraint(
        "ck_answer_single_training_context",
        "student_answers",
        "NOT (daily_task_item_id IS NOT NULL AND training_session_item_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_answer_single_training_context", "student_answers", type_="check"
    )
    op.drop_constraint(
        "uq_answer_training_session_item", "student_answers", type_="unique"
    )
    op.drop_index("ix_student_answers_training_session_item_id", table_name="student_answers")
    op.drop_constraint(
        "fk_student_answers_training_session_item", "student_answers", type_="foreignkey"
    )
    op.drop_column("student_answers", "training_session_item_id")
    op.drop_table("training_session_items")
    op.drop_table("training_sessions")
    sa.Enum(name="trainingsessionstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="trainingtype").drop(op.get_bind(), checkfirst=True)
