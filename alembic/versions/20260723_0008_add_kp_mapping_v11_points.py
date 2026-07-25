"""Add only the six kp-mapping-v1.1 knowledge points."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260723_0008"
down_revision: str | None = "20260723_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MAPPING_VERSION = "kp-mapping-v1.1"

# code, name, subject, parent_code
V11_ADDITIONS = [
    ("MATH-SET-OPERATIONS", "集合的基本运算", "数学", "MATH-SET"),
    (
        "PHY-KINEMATICS-UNIFORM-ACCELERATION",
        "匀变速直线运动规律",
        "物理",
        "PHY-KINEMATICS",
    ),
    ("PHY-OPTICS-REFRACTION", "光的折射规律", "物理", "PHY-OPTICS"),
    (
        "ENG-CLAUSE-RELATIVE-WORD-SELECTION",
        "定语从句关系词的选择",
        "英语",
        "ENG-CLAUSE",
    ),
    (
        "ENG-GRAMMAR-MODAL-BASIC",
        "情态动词的基本用法",
        "英语",
        "ENG-GRAMMAR",
    ),
    (
        "ENG-NONFINITE-GERUND-SUBJECT",
        "动名词短语作主语",
        "英语",
        "ENG-NONFINITE",
    ),
]


def _knowledge_table() -> sa.TableClause:
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


def seed_v11_additions(bind: sa.Connection) -> None:
    table = _knowledge_table()
    parent_codes = {parent_code for _, _, _, parent_code in V11_ADDITIONS}
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
    missing_parents = sorted(parent_codes - set(parents))
    if missing_parents:
        raise RuntimeError(f"Missing kp-mapping-v1.1 parent codes: {missing_parents}")

    rows: list[dict] = []
    for sort_order, (code, name, subject, parent_code) in enumerate(
        V11_ADDITIONS,
        start=100,
    ):
        parent = parents[parent_code]
        if parent.subject != subject or parent.level != 2 or not parent.is_active:
            raise RuntimeError(
                f"Invalid parent {parent_code} for kp-mapping-v1.1 code {code}"
            )
        rows.append(
            {
                "code": code,
                "name": name,
                "subject": subject,
                "parent_id": parent.id,
                "level": 3,
                "grade_scope": "高中",
                "sort_order": sort_order,
                "is_active": True,
            }
        )

    bind.execute(
        postgresql.insert(table)
        .values(rows)
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
                table.c.is_active,
            ).where(table.c.code.in_([row["code"] for row in rows]))
        )
    }
    missing = sorted({row["code"] for row in rows} - set(actual))
    if missing:
        raise RuntimeError(f"Missing kp-mapping-v1.1 codes after seed: {missing}")
    for expected in rows:
        row = actual[expected["code"]]
        actual_values = (
            row.name,
            row.subject,
            row.parent_id,
            row.level,
            row.is_active,
        )
        expected_values = (
            expected["name"],
            expected["subject"],
            expected["parent_id"],
            3,
            True,
        )
        if actual_values != expected_values:
            raise RuntimeError(
                f"Knowledge-point code {expected['code']} conflicts with kp-mapping-v1.1"
            )


def upgrade() -> None:
    seed_v11_additions(op.get_bind())


def downgrade() -> None:
    table = _knowledge_table()
    codes = [code for code, _, _, _ in V11_ADDITIONS]
    bind = op.get_bind()
    bind.execute(table.delete().where(table.c.code.in_(codes)))
    remaining = bind.scalar(
        sa.select(sa.func.count()).select_from(table).where(table.c.code.in_(codes))
    )
    if remaining:
        raise RuntimeError("kp-mapping-v1.1 rollback left added codes behind")
