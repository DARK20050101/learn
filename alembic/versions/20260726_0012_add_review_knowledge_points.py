"""Add knowledge points required by the first external-bank review."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260726_0012"
down_revision: str | None = "20260725_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

REVIEW_ADDITIONS = [
    (
        "MATH-VECTOR-DOT-PRODUCT",
        "平面向量数量积",
        "数学",
        "MATH-VECTOR",
        110,
    ),
    (
        "ENG-VOCAB-CONTEXT-ADVERB",
        "副词语境辨析",
        "英语",
        "ENG-VOCAB",
        110,
    ),
    (
        "ENG-VOCAB-SITUATIONAL-COMMUNICATION",
        "情景交际",
        "英语",
        "ENG-VOCAB",
        120,
    ),
]


def _table() -> sa.TableClause:
    return sa.table(
        "knowledge_points",
        sa.column("id", sa.Integer()),
        sa.column("code", sa.String()),
        sa.column("name", sa.String()),
        sa.column("subject", sa.String()),
        sa.column("parent_id", sa.Integer()),
        sa.column("level", sa.Integer()),
        sa.column("grade_scope", sa.String()),
        sa.column("sort_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )


def seed_review_additions(bind: sa.Connection) -> None:
    table = _table()
    parent_codes = {row[3] for row in REVIEW_ADDITIONS}
    parents = {
        row.code: row
        for row in bind.execute(
            sa.select(
                table.c.id,
                table.c.code,
                table.c.subject,
                table.c.level,
                table.c.is_active,
            ).where(table.c.code.in_(parent_codes))
        )
    }
    if set(parents) != parent_codes:
        raise RuntimeError(
            f"Missing review knowledge-point parents: {sorted(parent_codes - set(parents))}"
        )

    expected_rows = []
    for code, name, subject, parent_code, sort_order in REVIEW_ADDITIONS:
        parent = parents[parent_code]
        if parent.subject != subject or parent.level != 2 or not parent.is_active:
            raise RuntimeError(f"Invalid parent {parent_code} for {code}")
        expected_rows.append({
            "code": code,
            "name": name,
            "subject": subject,
            "parent_id": parent.id,
            "level": 3,
            "grade_scope": "高中",
            "sort_order": sort_order,
            "is_active": True,
        })

    bind.execute(
        postgresql.insert(table)
        .values(expected_rows)
        .on_conflict_do_nothing(index_elements=["code"])
    )
    actual = {
        row.code: row
        for row in bind.execute(
            sa.select(
                table.c.code,
                table.c.name,
                table.c.subject,
                table.c.parent_id,
                table.c.level,
                table.c.grade_scope,
                table.c.sort_order,
                table.c.is_active,
            ).where(table.c.code.in_([row["code"] for row in expected_rows]))
        )
    }
    for expected in expected_rows:
        row = actual.get(expected["code"])
        if row is None or dict(row._mapping) != expected:
            raise RuntimeError(
                f"Knowledge-point code {expected['code']} conflicts with review catalog"
            )


def upgrade() -> None:
    seed_review_additions(op.get_bind())


def downgrade() -> None:
    codes = [row[0] for row in REVIEW_ADDITIONS]
    table = _table()
    op.get_bind().execute(table.delete().where(table.c.code.in_(codes)))
