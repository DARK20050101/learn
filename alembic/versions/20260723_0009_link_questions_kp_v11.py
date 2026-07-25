"""Create the 60 kp-mapping-v1.1 primary question links only."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260723_0009"
down_revision: str | None = "20260723_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MAPPING_VERSION = "kp-mapping-v1.1"
SOURCE = "revision_c"

# Frozen Revision C mapping: question_id, active v1.1 primary code.
PRIMARY_MAPPINGS = [
    (1, "MATH-SET-OPERATIONS"),
    (2, "MATH-LOGIC-SUFFICIENT-NECESSARY"),
    (3, "MATH-FUNCTION-DOMAIN"),
    (4, "MATH-FUNCTION-MONOTONICITY"),
    (5, "MATH-FUNCTION-PARITY"),
    (6, "MATH-EXPONENT-OPERATION"),
    (7, "MATH-LOGARITHM-OPERATION"),
    (8, "MATH-TRIG-SPECIAL-ANGLE"),
    (9, "MATH-TRIG-FUNDAMENTAL-IDENTITY"),
    (10, "MATH-VECTOR-COORDINATE"),
    (11, "MATH-SEQUENCE-ARITHMETIC-GENERAL"),
    (12, "MATH-SEQUENCE-GEOMETRIC-GENERAL"),
    (13, "MATH-INEQUALITY-QUADRATIC"),
    (14, "MATH-SOLID-LINE-PLANE-PERPENDICULAR"),
    (15, "MATH-ANALYTIC-LINE-SLOPE"),
    (16, "MATH-ANALYTIC-CIRCLE-STANDARD"),
    (17, "MATH-PROBABILITY-CLASSICAL"),
    (18, "MATH-STATISTICS-MEAN"),
    (19, "MATH-DERIVATIVE-ELEMENTARY"),
    (20, "MATH-COMPLEX-ARITHMETIC"),
    (21, "PHY-MOTION-PARTICLE-MODEL"),
    (22, "PHY-MOTION-DISPLACEMENT-DISTANCE"),
    (23, "PHY-KINEMATICS-UNIFORM-ACCELERATION"),
    (24, "PHY-KINEMATICS-FREE-FALL"),
    (25, "PHY-FORCE-COMPOSITION"),
    (26, "PHY-NEWTON-THIRD-LAW"),
    (27, "PHY-NEWTON-SECOND-LAW"),
    (28, "PHY-PROJECTILE-HORIZONTAL"),
    (29, "PHY-CIRCULAR-CENTRIPETAL-ACCELERATION"),
    (30, "PHY-GRAVITY-UNIVERSAL-LAW"),
    (31, "PHY-WORK-ENERGY-WORK-CALCULATION"),
    (32, "PHY-WORK-ENERGY-KINETIC"),
    (33, "PHY-MOMENTUM-BASIC"),
    (34, "PHY-ELECTROSTATICS-COULOMB-LAW"),
    (35, "PHY-CIRCUIT-OHM-LAW"),
    (36, "PHY-CIRCUIT-ELECTRIC-POWER"),
    (37, "PHY-MAGNETIC-FIELD-DIRECTION"),
    (38, "PHY-INDUCTION-CURRENT-CONDITION"),
    (39, "PHY-WAVE-SPEED-FREQUENCY-WAVELENGTH"),
    (40, "PHY-OPTICS-REFRACTION"),
    (41, "ENG-VOCAB-COLLOCATION"),
    (42, "ENG-VOCAB-CONTEXT-VERB"),
    (43, "ENG-GRAMMAR-TENSE-PRESENT-SIMPLE"),
    (44, "ENG-GRAMMAR-TENSE-PRESENT-PERFECT"),
    (45, "ENG-GRAMMAR-TENSE-PAST-CONTINUOUS"),
    (46, "ENG-GRAMMAR-VOICE-PRESENT-PASSIVE"),
    (47, "ENG-NONFINITE-INFINITIVE"),
    (48, "ENG-NONFINITE-INFINITIVE"),
    (49, "ENG-CLAUSE-RELATIVE-WORD-SELECTION"),
    (50, "ENG-CLAUSE-RELATIVE-WORD-SELECTION"),
    (51, "ENG-CLAUSE-OBJECT-WORD-ORDER"),
    (52, "ENG-CLAUSE-ADVERBIAL-CONDITION"),
    (53, "ENG-GRAMMAR-MODAL-BASIC"),
    (54, "ENG-GRAMMAR-AGREEMENT-PROXIMITY"),
    (55, "ENG-GRAMMAR-ADJECTIVE-COMPARATIVE"),
    (56, "ENG-VOCAB-COLLOCATION"),
    (57, "ENG-READING-DETAIL"),
    (58, "ENG-READING-MAIN-IDEA"),
    (59, "ENG-GRAMMAR-THERE-BE"),
    (60, "ENG-NONFINITE-GERUND-SUBJECT"),
]


def _questions_table() -> sa.TableClause:
    return sa.table(
        "questions",
        sa.column("id", sa.Integer()),
        sa.column("subject", sa.String()),
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


def _links_table() -> sa.TableClause:
    return sa.table(
        "question_knowledge_points",
        sa.column("id", sa.Integer()),
        sa.column("question_id", sa.Integer()),
        sa.column("knowledge_point_id", sa.Integer()),
        sa.column("role", sa.String()),
        sa.column("weight", sa.Float()),
        sa.column("source", sa.String()),
        sa.column("mapping_version", sa.String()),
    )


def seed_primary_links(bind: sa.Connection) -> None:
    question_ids = [question_id for question_id, _ in PRIMARY_MAPPINGS]
    codes = [code for _, code in PRIMARY_MAPPINGS]
    if len(PRIMARY_MAPPINGS) != 60 or set(question_ids) != set(range(1, 61)):
        raise RuntimeError("Revision C mapping must contain question IDs 1 through 60 once")

    questions = _questions_table()
    knowledge_points = _knowledge_points_table()
    links = _links_table()

    question_rows = {
        row.id: row
        for row in bind.execute(
            sa.select(questions.c.id, questions.c.subject).where(
                questions.c.id.in_(question_ids)
            )
        )
    }
    missing_questions = sorted(set(question_ids) - set(question_rows))
    if missing_questions:
        raise RuntimeError(f"Revision C missing questions: {missing_questions}")

    knowledge_rows = {
        row.code: row
        for row in bind.execute(
            sa.select(
                knowledge_points.c.id,
                knowledge_points.c.code,
                knowledge_points.c.subject,
                knowledge_points.c.level,
                knowledge_points.c.is_active,
            ).where(knowledge_points.c.code.in_(set(codes)))
        )
    }
    missing_codes = sorted(set(codes) - set(knowledge_rows))
    if missing_codes:
        raise RuntimeError(f"Revision C missing knowledge-point codes: {missing_codes}")

    invalid_codes = sorted(
        code
        for code, row in knowledge_rows.items()
        if row.level != 3 or not row.is_active
    )
    if invalid_codes:
        raise RuntimeError(
            f"Revision C target codes must be active level-3 nodes: {invalid_codes}"
        )

    expected_by_question: dict[int, int] = {}
    rows_to_insert: list[dict] = []
    for question_id, code in PRIMARY_MAPPINGS:
        question = question_rows[question_id]
        knowledge_point = knowledge_rows[code]
        if question.subject != knowledge_point.subject:
            raise RuntimeError(
                f"Revision C subject conflict for question {question_id}: {code}"
            )
        expected_by_question[question_id] = knowledge_point.id
        rows_to_insert.append(
            {
                "question_id": question_id,
                "knowledge_point_id": knowledge_point.id,
                "role": "primary",
                "weight": 1.0,
                "source": SOURCE,
                "mapping_version": MAPPING_VERSION,
            }
        )

    existing_primary = {
        row.question_id: row
        for row in bind.execute(
            sa.select(
                links.c.question_id,
                links.c.knowledge_point_id,
                links.c.role,
                links.c.weight,
                links.c.source,
                links.c.mapping_version,
            ).where(
                links.c.question_id.in_(question_ids),
                links.c.role == "primary",
            )
        )
    }
    for question_id, row in existing_primary.items():
        expected = (
            expected_by_question[question_id],
            "primary",
            1.0,
            SOURCE,
            MAPPING_VERSION,
        )
        actual = (
            row.knowledge_point_id,
            row.role,
            row.weight,
            row.source,
            row.mapping_version,
        )
        if actual != expected:
            raise RuntimeError(
                f"Revision C primary conflict for question {question_id}"
            )

    bind.execute(
        postgresql.insert(links)
        .values(rows_to_insert)
        .on_conflict_do_nothing(
            index_elements=["question_id", "knowledge_point_id"]
        )
    )

    actual_primary = {
        row.question_id: row
        for row in bind.execute(
            sa.select(
                links.c.question_id,
                links.c.knowledge_point_id,
                links.c.role,
                links.c.weight,
                links.c.source,
                links.c.mapping_version,
            ).where(
                links.c.question_id.in_(question_ids),
                links.c.role == "primary",
            )
        )
    }
    if set(actual_primary) != set(question_ids):
        missing = sorted(set(question_ids) - set(actual_primary))
        raise RuntimeError(f"Revision C missing primary links after seed: {missing}")
    for question_id, row in actual_primary.items():
        expected = (
            expected_by_question[question_id],
            "primary",
            1.0,
            SOURCE,
            MAPPING_VERSION,
        )
        actual = (
            row.knowledge_point_id,
            row.role,
            row.weight,
            row.source,
            row.mapping_version,
        )
        if actual != expected:
            raise RuntimeError(
                f"Revision C primary link mismatch for question {question_id}"
            )


def upgrade() -> None:
    seed_primary_links(op.get_bind())


def downgrade() -> None:
    links = _links_table()
    bind = op.get_bind()
    question_ids = [question_id for question_id, _ in PRIMARY_MAPPINGS]
    bind.execute(
        links.delete().where(
            links.c.question_id.in_(question_ids),
            links.c.role == "primary",
            links.c.source == SOURCE,
            links.c.mapping_version == MAPPING_VERSION,
        )
    )
    remaining = bind.scalar(
        sa.select(sa.func.count())
        .select_from(links)
        .where(
            links.c.question_id.in_(question_ids),
            links.c.role == "primary",
            links.c.source == SOURCE,
            links.c.mapping_version == MAPPING_VERSION,
        )
    )
    if remaining:
        raise RuntimeError("Revision C rollback left migrated primary links behind")
