"""Add fill_review training type for concept memorization drills."""

from collections.abc import Sequence

from alembic import op

revision: str = "20260803_0015"
down_revision: str | None = "20260803_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE trainingtype ADD VALUE IF NOT EXISTS 'fill_review'")


def downgrade() -> None:
    # PostgreSQL does not support removing a single enum value. Existing
    # fill_review sessions would need to be migrated to another type first,
    # then the enum recreated with CREATE TYPE ... ; ALTER COLUMN ... ; DROP TYPE.
    pass
