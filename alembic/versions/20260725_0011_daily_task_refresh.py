"""Add bounded refresh state to daily tasks."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260725_0011"
down_revision: str | None = "20260723_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "daily_tasks",
        sa.Column("version", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "daily_tasks",
        sa.Column("refresh_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "daily_tasks",
        sa.Column("refreshed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_daily_task_version",
        "daily_tasks",
        "version BETWEEN 1 AND 2",
    )
    op.create_check_constraint(
        "ck_daily_task_refresh_count",
        "daily_tasks",
        "refresh_count BETWEEN 0 AND 1",
    )
    op.create_check_constraint(
        "ck_daily_task_refresh_version",
        "daily_tasks",
        "version = refresh_count + 1",
    )


def downgrade() -> None:
    op.drop_constraint("ck_daily_task_refresh_version", "daily_tasks", type_="check")
    op.drop_constraint("ck_daily_task_refresh_count", "daily_tasks", type_="check")
    op.drop_constraint("ck_daily_task_version", "daily_tasks", type_="check")
    op.drop_column("daily_tasks", "refreshed_at")
    op.drop_column("daily_tasks", "refresh_count")
    op.drop_column("daily_tasks", "version")
