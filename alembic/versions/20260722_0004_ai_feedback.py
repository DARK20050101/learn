"""Add AI knowledge gap count and student difficulty feedback."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260722_0004"
down_revision: str | None = "20260722_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    difficulty_feedback_type = postgresql.ENUM(
        "easy", "difficult", "dont_know", name="difficultyfeedback"
    )
    difficulty_feedback_type.create(op.get_bind(), checkfirst=True)
    difficulty_feedback_column = postgresql.ENUM(
        "easy",
        "difficult",
        "dont_know",
        name="difficultyfeedback",
        create_type=False,
    )
    op.add_column(
        "knowledge_status",
        sa.Column("ai_gap_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "student_answers",
        sa.Column("difficulty_feedback", difficulty_feedback_column, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("student_answers", "difficulty_feedback")
    op.drop_column("knowledge_status", "ai_gap_count")
    sa.Enum(name="difficultyfeedback").drop(op.get_bind(), checkfirst=True)
