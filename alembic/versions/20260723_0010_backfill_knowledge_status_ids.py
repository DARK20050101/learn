"""Backfill only the 18 knowledge_status standard knowledge-point IDs."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260723_0010"
down_revision: str | None = "20260723_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MAPPING_VERSION = "kp-mapping-v1.1"

# status_id, user_id, subject, legacy knowledge_point, target code
STATUS_MAPPINGS = [
    (1, 1, "英语", "动词辨析", "ENG-VOCAB-COLLOCATION"),
    (2, 1, "英语", "形容词辨析", "ENG-VOCAB-CONTEXT-VERB"),
    (3, 1, "英语", "现在完成时", "ENG-GRAMMAR-TENSE-PRESENT-PERFECT"),
    (4, 1, "物理", "位移与路程", "PHY-MOTION-DISPLACEMENT-DISTANCE"),
    (5, 1, "物理", "速度公式", "PHY-KINEMATICS-UNIFORM-ACCELERATION"),
    (6, 1, "数学", "充分条件与必要条件", "MATH-LOGIC-SUFFICIENT-NECESSARY"),
    (7, 2, "英语", "动词辨析", "ENG-VOCAB-COLLOCATION"),
    (8, 2, "英语", "形容词辨析", "ENG-VOCAB-CONTEXT-VERB"),
    (9, 2, "英语", "现在完成时", "ENG-GRAMMAR-TENSE-PRESENT-PERFECT"),
    (10, 2, "物理", "位移与路程", "PHY-MOTION-DISPLACEMENT-DISTANCE"),
    (11, 2, "物理", "速度公式", "PHY-KINEMATICS-UNIFORM-ACCELERATION"),
    (12, 2, "数学", "充分条件与必要条件", "MATH-LOGIC-SUFFICIENT-NECESSARY"),
    (13, 2, "数学", "集合的交集", "MATH-SET-OPERATIONS"),
    (14, 2, "数学", "一元二次不等式", "MATH-INEQUALITY-QUADRATIC"),
    (15, 2, "数学", "函数定义域", "MATH-FUNCTION-DOMAIN"),
    (16, 2, "数学", "函数单调性", "MATH-FUNCTION-MONOTONICITY"),
    (17, 2, "数学", "函数奇偶性", "MATH-FUNCTION-PARITY"),
    (18, 2, "数学", "对数运算", "MATH-LOGARITHM-OPERATION"),
]


def _status_table() -> sa.TableClause:
    return sa.table(
        "knowledge_status",
        sa.column("id", sa.Integer()),
        sa.column("user_id", sa.Integer()),
        sa.column("subject", sa.String()),
        sa.column("knowledge_point", sa.String()),
        sa.column("knowledge_point_id", sa.Integer()),
        sa.column("mapping_version", sa.String()),
        sa.column("mapped_at", sa.DateTime(timezone=True)),
    )


def _knowledge_points_table() -> sa.TableClause:
    return sa.table(
        "knowledge_points",
        sa.column("id", sa.Integer()),
        sa.column("code", sa.String()),
        sa.column("subject", sa.String()),
        sa.column("level", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )


def backfill_status_ids(bind: sa.Connection) -> None:
    status_ids = [row[0] for row in STATUS_MAPPINGS]
    if len(STATUS_MAPPINGS) != 18 or set(status_ids) != set(range(1, 19)):
        raise RuntimeError("Revision D1 mapping must contain status IDs 1 through 18 once")

    statuses = _status_table()
    knowledge_points = _knowledge_points_table()
    actual_statuses = {
        row.id: row
        for row in bind.execute(
            sa.select(
                statuses.c.id,
                statuses.c.user_id,
                statuses.c.subject,
                statuses.c.knowledge_point,
                statuses.c.knowledge_point_id,
                statuses.c.mapping_version,
                statuses.c.mapped_at,
            ).where(statuses.c.id.in_(status_ids))
        )
    }
    missing_statuses = sorted(set(status_ids) - set(actual_statuses))
    if missing_statuses:
        raise RuntimeError(f"Revision D1 missing statuses: {missing_statuses}")

    target_codes = {row[4] for row in STATUS_MAPPINGS}
    targets = {
        row.code: row
        for row in bind.execute(
            sa.select(
                knowledge_points.c.id,
                knowledge_points.c.code,
                knowledge_points.c.subject,
                knowledge_points.c.level,
                knowledge_points.c.is_active,
            ).where(knowledge_points.c.code.in_(target_codes))
        )
    }
    missing_codes = sorted(target_codes - set(targets))
    if missing_codes:
        raise RuntimeError(
            f"Revision D1 missing knowledge-point codes: {missing_codes}"
        )

    for status_id, user_id, subject, legacy_name, code in STATUS_MAPPINGS:
        status = actual_statuses[status_id]
        target = targets[code]
        legacy_identity = (
            status.user_id,
            status.subject,
            status.knowledge_point,
        )
        if legacy_identity != (user_id, subject, legacy_name):
            raise RuntimeError(f"Revision D1 legacy conflict for status {status_id}")
        if target.subject != subject or target.level != 3 or not target.is_active:
            raise RuntimeError(f"Revision D1 invalid target {code} for status {status_id}")

        mapping_state = (
            status.knowledge_point_id,
            status.mapping_version,
            status.mapped_at,
        )
        is_unmapped = mapping_state == (None, None, None)
        is_consistent = (
            status.knowledge_point_id == target.id
            and status.mapping_version == MAPPING_VERSION
            and status.mapped_at is not None
        )
        if is_consistent:
            continue
        if not is_unmapped:
            raise RuntimeError(f"Revision D1 mapping conflict for status {status_id}")

        bind.execute(
            statuses.update()
            .where(statuses.c.id == status_id)
            .values(
                knowledge_point_id=target.id,
                mapping_version=MAPPING_VERSION,
                mapped_at=sa.func.now(),
            )
        )

    verified = {
        row.id: row
        for row in bind.execute(
            sa.select(
                statuses.c.id,
                statuses.c.knowledge_point_id,
                statuses.c.mapping_version,
                statuses.c.mapped_at,
            ).where(statuses.c.id.in_(status_ids))
        )
    }
    for status_id, _, _, _, code in STATUS_MAPPINGS:
        row = verified[status_id]
        if (
            row.knowledge_point_id != targets[code].id
            or row.mapping_version != MAPPING_VERSION
            or row.mapped_at is None
        ):
            raise RuntimeError(f"Revision D1 verification failed for status {status_id}")


def upgrade() -> None:
    backfill_status_ids(op.get_bind())


def downgrade() -> None:
    statuses = _status_table()
    knowledge_points = _knowledge_points_table()
    bind = op.get_bind()
    target_codes = {row[4] for row in STATUS_MAPPINGS}
    target_ids = {
        row.code: row.id
        for row in bind.execute(
            sa.select(knowledge_points.c.id, knowledge_points.c.code).where(
                knowledge_points.c.code.in_(target_codes)
            )
        )
    }
    if set(target_ids) != target_codes:
        raise RuntimeError("Revision D1 rollback cannot resolve all target codes")

    for status_id, _, _, _, code in STATUS_MAPPINGS:
        row = bind.execute(
            sa.select(
                statuses.c.knowledge_point_id,
                statuses.c.mapping_version,
                statuses.c.mapped_at,
            ).where(statuses.c.id == status_id)
        ).one_or_none()
        if row is None:
            raise RuntimeError(f"Revision D1 rollback missing status {status_id}")
        if (
            row.knowledge_point_id != target_ids[code]
            or row.mapping_version != MAPPING_VERSION
            or row.mapped_at is None
        ):
            raise RuntimeError(f"Revision D1 rollback conflict for status {status_id}")
        bind.execute(
            statuses.update()
            .where(statuses.c.id == status_id)
            .values(
                knowledge_point_id=None,
                mapping_version=None,
                mapped_at=None,
            )
        )
