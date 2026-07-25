"""Add question import fields and batch logs."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260722_0002"
down_revision: str | None = "20260722_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    import_status = sa.Enum(
        "processing",
        "completed",
        "completed_with_errors",
        "failed",
        name="importstatus",
    )
    op.add_column("questions", sa.Column("chapter", sa.String(100), nullable=True))
    op.add_column("questions", sa.Column("source", sa.String(255), nullable=True))
    op.add_column("questions", sa.Column("content_hash", sa.String(64), nullable=True))
    op.create_index("ix_questions_chapter", "questions", ["chapter"])
    op.create_index("ix_questions_content_hash", "questions", ["content_hash"], unique=True)

    op.create_table(
        "question_import_batches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("status", import_status, nullable=False, server_default="processing"),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("errors", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_question_import_batches_file_hash", "question_import_batches", ["file_hash"]
    )
    op.create_index("ix_question_import_batches_status", "question_import_batches", ["status"])


def downgrade() -> None:
    op.drop_table("question_import_batches")
    op.drop_index("ix_questions_content_hash", table_name="questions")
    op.drop_index("ix_questions_chapter", table_name="questions")
    op.drop_column("questions", "content_hash")
    op.drop_column("questions", "source")
    op.drop_column("questions", "chapter")
    sa.Enum(name="importstatus").drop(op.get_bind(), checkfirst=True)
