"""Add fill_blank question type."""

from collections.abc import Sequence

from alembic import op

revision: str = "20260803_0014"
down_revision: str | None = "20260730_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE questiontype ADD VALUE IF NOT EXISTS 'fill_blank'")


def downgrade() -> None:
    # PostgreSQL does not support removing a single enum value. Existing
    # fill_blank rows would need to be migrated to another type first, then
    # the enum recreated with CREATE TYPE ... ; ALTER COLUMN ... ; DROP TYPE.
    pass
