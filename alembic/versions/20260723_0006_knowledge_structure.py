"""Add the normalized knowledge-point foundation without migrating data."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260723_0006"
down_revision: str | None = "20260723_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "knowledge_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("subject", sa.String(50), nullable=False),
        sa.Column(
            "parent_id",
            sa.Integer(),
            sa.ForeignKey("knowledge_points.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("grade_scope", sa.String(30), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.UniqueConstraint("code", name="uq_knowledge_points_code"),
        sa.CheckConstraint("level BETWEEN 1 AND 3", name="ck_knowledge_point_level"),
    )
    op.create_index("ix_knowledge_points_code", "knowledge_points", ["code"])
    op.create_index("ix_knowledge_points_subject", "knowledge_points", ["subject"])
    op.create_index("ix_knowledge_points_parent_id", "knowledge_points", ["parent_id"])
    op.create_index("ix_knowledge_points_level", "knowledge_points", ["level"])
    op.create_index("ix_knowledge_points_is_active", "knowledge_points", ["is_active"])

    op.create_table(
        "knowledge_point_aliases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "knowledge_point_id",
            sa.Integer(),
            sa.ForeignKey("knowledge_points.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject", sa.String(50), nullable=False),
        sa.Column("alias", sa.String(100), nullable=False),
        sa.Column("normalized_alias", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        *timestamps(),
        sa.UniqueConstraint(
            "subject",
            "normalized_alias",
            name="uq_knowledge_point_alias_subject_normalized",
        ),
    )
    op.create_index(
        "ix_knowledge_point_aliases_knowledge_point_id",
        "knowledge_point_aliases",
        ["knowledge_point_id"],
    )
    op.create_index(
        "ix_knowledge_point_aliases_subject",
        "knowledge_point_aliases",
        ["subject"],
    )
    op.create_index(
        "ix_knowledge_point_aliases_is_active",
        "knowledge_point_aliases",
        ["is_active"],
    )

    op.create_table(
        "question_knowledge_points",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "question_id",
            sa.Integer(),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "knowledge_point_id",
            sa.Integer(),
            sa.ForeignKey("knowledge_points.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("source", sa.String(30), nullable=True),
        sa.Column("mapping_version", sa.String(30), nullable=True),
        *timestamps(),
        sa.UniqueConstraint(
            "question_id",
            "knowledge_point_id",
            name="uq_question_knowledge_point",
        ),
        sa.CheckConstraint(
            "role IN ('primary', 'secondary')",
            name="ck_question_knowledge_point_role",
        ),
        sa.CheckConstraint(
            "weight > 0 AND weight <= 1",
            name="ck_question_knowledge_point_weight",
        ),
    )
    op.create_index(
        "ix_question_knowledge_points_question_id",
        "question_knowledge_points",
        ["question_id"],
    )
    op.create_index(
        "ix_question_knowledge_points_knowledge_point_id",
        "question_knowledge_points",
        ["knowledge_point_id"],
    )
    op.create_index(
        "uq_question_primary_knowledge_point",
        "question_knowledge_points",
        ["question_id"],
        unique=True,
        postgresql_where=sa.text("role = 'primary'"),
    )

    op.create_table(
        "knowledge_status_migration_backups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("migration_batch", sa.String(50), nullable=False),
        sa.Column("original_status_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(50), nullable=True),
        sa.Column("knowledge_point", sa.String(100), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=True),
        sa.Column("correct_count", sa.Integer(), nullable=True),
        sa.Column("ai_gap_count", sa.Integer(), nullable=True),
        sa.Column("mastery_score", sa.Float(), nullable=True),
        sa.Column("last_practiced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "target_knowledge_point_id",
            sa.Integer(),
            sa.ForeignKey("knowledge_points.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("mapping_version", sa.String(30), nullable=True),
        sa.Column("merge_target_status_id", sa.Integer(), nullable=True),
        sa.Column("backup_reason", sa.String(255), nullable=True),
        *timestamps(),
        sa.UniqueConstraint(
            "migration_batch",
            "original_status_id",
            name="uq_knowledge_status_backup_batch_original",
        ),
    )
    op.create_index(
        "ix_knowledge_status_migration_backups_migration_batch",
        "knowledge_status_migration_backups",
        ["migration_batch"],
    )
    op.create_index(
        "ix_knowledge_status_migration_backups_original_status_id",
        "knowledge_status_migration_backups",
        ["original_status_id"],
    )
    op.create_index(
        "ix_knowledge_status_migration_backups_user_id",
        "knowledge_status_migration_backups",
        ["user_id"],
    )
    op.create_index(
        "ix_knowledge_status_migration_backups_target_knowledge_point_id",
        "knowledge_status_migration_backups",
        ["target_knowledge_point_id"],
    )

    op.add_column(
        "knowledge_status",
        sa.Column("knowledge_point_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "knowledge_status",
        sa.Column("mapping_version", sa.String(30), nullable=True),
    )
    op.add_column(
        "knowledge_status",
        sa.Column("mapped_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_knowledge_status_standard_knowledge_point",
        "knowledge_status",
        "knowledge_points",
        ["knowledge_point_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_knowledge_status_knowledge_point_id",
        "knowledge_status",
        ["knowledge_point_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_status_knowledge_point_id", table_name="knowledge_status")
    op.drop_constraint(
        "fk_knowledge_status_standard_knowledge_point",
        "knowledge_status",
        type_="foreignkey",
    )
    op.drop_column("knowledge_status", "mapped_at")
    op.drop_column("knowledge_status", "mapping_version")
    op.drop_column("knowledge_status", "knowledge_point_id")
    op.drop_table("knowledge_status_migration_backups")
    op.drop_table("question_knowledge_points")
    op.drop_table("knowledge_point_aliases")
    op.drop_table("knowledge_points")
