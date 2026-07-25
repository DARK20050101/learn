"""Prevent duplicate questions within one daily task."""

from collections.abc import Sequence

from alembic import op

revision: str = "20260722_0003"
down_revision: str | None = "20260722_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_task_item_question",
        "daily_task_items",
        ["daily_task_id", "question_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_task_item_question", "daily_task_items", type_="unique")
