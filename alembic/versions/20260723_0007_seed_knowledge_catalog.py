"""Seed the kp-mapping-v1 knowledge-point catalog without linking questions."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260723_0007"
down_revision: str | None = "20260723_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

MAPPING_VERSION = "kp-mapping-v1"

# code, name, subject, parent_code
LEVEL_ONE = [
    ("MATH", "数学", "数学", None),
    ("PHY", "物理", "物理", None),
    ("ENG", "英语", "英语", None),
]

LEVEL_TWO = [
    ("MATH-SET", "集合与逻辑", "数学", "MATH"),
    ("MATH-LOGIC", "常用逻辑用语", "数学", "MATH"),
    ("MATH-FUNCTION", "函数", "数学", "MATH"),
    ("MATH-EXPONENT", "指数与对数", "数学", "MATH"),
    ("MATH-TRIG", "三角函数", "数学", "MATH"),
    ("MATH-VECTOR", "平面向量", "数学", "MATH"),
    ("MATH-SEQUENCE", "数列", "数学", "MATH"),
    ("MATH-INEQUALITY", "不等式", "数学", "MATH"),
    ("MATH-SOLID", "立体几何", "数学", "MATH"),
    ("MATH-ANALYTIC", "解析几何", "数学", "MATH"),
    ("MATH-PROBABILITY", "概率", "数学", "MATH"),
    ("MATH-STATISTICS", "统计", "数学", "MATH"),
    ("MATH-DERIVATIVE", "导数", "数学", "MATH"),
    ("MATH-COMPLEX", "复数", "数学", "MATH"),
    ("PHY-MOTION", "运动的描述", "物理", "PHY"),
    ("PHY-KINEMATICS", "直线运动", "物理", "PHY"),
    ("PHY-FORCE", "相互作用", "物理", "PHY"),
    ("PHY-NEWTON", "牛顿运动定律", "物理", "PHY"),
    ("PHY-PROJECTILE", "曲线运动", "物理", "PHY"),
    ("PHY-CIRCULAR", "圆周运动", "物理", "PHY"),
    ("PHY-GRAVITY", "万有引力", "物理", "PHY"),
    ("PHY-WORK-ENERGY", "功和能", "物理", "PHY"),
    ("PHY-MOMENTUM", "动量", "物理", "PHY"),
    ("PHY-ELECTROSTATICS", "静电场", "物理", "PHY"),
    ("PHY-CIRCUIT", "恒定电流", "物理", "PHY"),
    ("PHY-MAGNETIC-FIELD", "磁场", "物理", "PHY"),
    ("PHY-INDUCTION", "电磁感应", "物理", "PHY"),
    ("PHY-WAVE", "机械振动与机械波", "物理", "PHY"),
    ("PHY-OPTICS", "光学", "物理", "PHY"),
    ("ENG-VOCAB", "词汇", "英语", "ENG"),
    ("ENG-GRAMMAR", "语法", "英语", "ENG"),
    ("ENG-NONFINITE", "非谓语动词", "英语", "ENG"),
    ("ENG-CLAUSE", "从句", "英语", "ENG"),
    ("ENG-READING", "阅读理解", "英语", "ENG"),
    ("ENG-WRITING", "书面表达", "英语", "ENG"),
]

LEVEL_THREE = [
    ("MATH-SET-INTERSECTION", "集合的基本运算（交集）", "数学", "MATH-SET"),
    (
        "MATH-LOGIC-SUFFICIENT-NECESSARY",
        "充分条件与必要条件",
        "数学",
        "MATH-LOGIC",
    ),
    ("MATH-FUNCTION-DOMAIN", "函数的定义域", "数学", "MATH-FUNCTION"),
    ("MATH-FUNCTION-MONOTONICITY", "函数的单调性", "数学", "MATH-FUNCTION"),
    ("MATH-FUNCTION-PARITY", "函数的奇偶性", "数学", "MATH-FUNCTION"),
    ("MATH-EXPONENT-OPERATION", "指数运算", "数学", "MATH-EXPONENT"),
    ("MATH-LOGARITHM-OPERATION", "对数运算", "数学", "MATH-EXPONENT"),
    ("MATH-TRIG-SPECIAL-ANGLE", "特殊角的三角函数值", "数学", "MATH-TRIG"),
    (
        "MATH-TRIG-FUNDAMENTAL-IDENTITY",
        "同角三角函数的基本关系",
        "数学",
        "MATH-TRIG",
    ),
    ("MATH-VECTOR-COORDINATE", "平面向量的坐标运算", "数学", "MATH-VECTOR"),
    (
        "MATH-SEQUENCE-ARITHMETIC-GENERAL",
        "等差数列的通项公式",
        "数学",
        "MATH-SEQUENCE",
    ),
    (
        "MATH-SEQUENCE-GEOMETRIC-GENERAL",
        "等比数列的通项公式",
        "数学",
        "MATH-SEQUENCE",
    ),
    (
        "MATH-INEQUALITY-QUADRATIC",
        "一元二次不等式的解法",
        "数学",
        "MATH-INEQUALITY",
    ),
    (
        "MATH-SOLID-LINE-PLANE-PERPENDICULAR",
        "直线与平面垂直的判定",
        "数学",
        "MATH-SOLID",
    ),
    ("MATH-ANALYTIC-LINE-SLOPE", "直线的斜率", "数学", "MATH-ANALYTIC"),
    (
        "MATH-ANALYTIC-CIRCLE-STANDARD",
        "圆的标准方程",
        "数学",
        "MATH-ANALYTIC",
    ),
    (
        "MATH-PROBABILITY-CLASSICAL",
        "古典概型",
        "数学",
        "MATH-PROBABILITY",
    ),
    ("MATH-STATISTICS-MEAN", "平均数", "数学", "MATH-STATISTICS"),
    (
        "MATH-DERIVATIVE-ELEMENTARY",
        "基本初等函数的导数",
        "数学",
        "MATH-DERIVATIVE",
    ),
    ("MATH-COMPLEX-ARITHMETIC", "复数的四则运算", "数学", "MATH-COMPLEX"),
    ("PHY-MOTION-PARTICLE-MODEL", "质点模型", "物理", "PHY-MOTION"),
    (
        "PHY-MOTION-DISPLACEMENT-DISTANCE",
        "位移与路程",
        "物理",
        "PHY-MOTION",
    ),
    (
        "PHY-KINEMATICS-VELOCITY-EQUATION",
        "匀变速直线运动速度公式",
        "物理",
        "PHY-KINEMATICS",
    ),
    ("PHY-KINEMATICS-FREE-FALL", "自由落体运动", "物理", "PHY-KINEMATICS"),
    ("PHY-FORCE-COMPOSITION", "力的合成", "物理", "PHY-FORCE"),
    ("PHY-NEWTON-THIRD-LAW", "牛顿第三定律", "物理", "PHY-NEWTON"),
    ("PHY-NEWTON-SECOND-LAW", "牛顿第二定律", "物理", "PHY-NEWTON"),
    ("PHY-PROJECTILE-HORIZONTAL", "平抛运动规律", "物理", "PHY-PROJECTILE"),
    (
        "PHY-CIRCULAR-CENTRIPETAL-ACCELERATION",
        "向心加速度",
        "物理",
        "PHY-CIRCULAR",
    ),
    ("PHY-GRAVITY-UNIVERSAL-LAW", "万有引力定律", "物理", "PHY-GRAVITY"),
    (
        "PHY-WORK-ENERGY-WORK-CALCULATION",
        "功的计算",
        "物理",
        "PHY-WORK-ENERGY",
    ),
    (
        "PHY-WORK-ENERGY-KINETIC",
        "动能概念与计算",
        "物理",
        "PHY-WORK-ENERGY",
    ),
    ("PHY-MOMENTUM-BASIC", "动量概念与计算", "物理", "PHY-MOMENTUM"),
    (
        "PHY-ELECTROSTATICS-COULOMB-LAW",
        "库仑定律",
        "物理",
        "PHY-ELECTROSTATICS",
    ),
    ("PHY-CIRCUIT-OHM-LAW", "欧姆定律", "物理", "PHY-CIRCUIT"),
    ("PHY-CIRCUIT-ELECTRIC-POWER", "电功率的计算", "物理", "PHY-CIRCUIT"),
    (
        "PHY-MAGNETIC-FIELD-DIRECTION",
        "磁场方向的判定",
        "物理",
        "PHY-MAGNETIC-FIELD",
    ),
    (
        "PHY-INDUCTION-CURRENT-CONDITION",
        "感应电流的产生条件",
        "物理",
        "PHY-INDUCTION",
    ),
    (
        "PHY-WAVE-SPEED-FREQUENCY-WAVELENGTH",
        "波速、波长与频率的关系",
        "物理",
        "PHY-WAVE",
    ),
    (
        "PHY-OPTICS-REFRACTION-PHENOMENON",
        "光的折射现象",
        "物理",
        "PHY-OPTICS",
    ),
    ("ENG-VOCAB-COLLOCATION", "固定搭配", "英语", "ENG-VOCAB"),
    ("ENG-VOCAB-CONTEXT-VERB", "动词语境辨析", "英语", "ENG-VOCAB"),
    (
        "ENG-GRAMMAR-TENSE-PRESENT-SIMPLE",
        "一般现在时",
        "英语",
        "ENG-GRAMMAR",
    ),
    (
        "ENG-GRAMMAR-TENSE-PRESENT-PERFECT",
        "现在完成时",
        "英语",
        "ENG-GRAMMAR",
    ),
    (
        "ENG-GRAMMAR-TENSE-PAST-CONTINUOUS",
        "过去进行时",
        "英语",
        "ENG-GRAMMAR",
    ),
    (
        "ENG-GRAMMAR-VOICE-PRESENT-PASSIVE",
        "一般现在时被动语态",
        "英语",
        "ENG-GRAMMAR",
    ),
    ("ENG-NONFINITE-INFINITIVE", "动词不定式", "英语", "ENG-NONFINITE"),
    (
        "ENG-CLAUSE-RELATIVE-THAT",
        "关系代词 that 的用法",
        "英语",
        "ENG-CLAUSE",
    ),
    (
        "ENG-CLAUSE-RELATIVE-WHERE",
        "关系副词 where 的用法",
        "英语",
        "ENG-CLAUSE",
    ),
    (
        "ENG-CLAUSE-OBJECT-WORD-ORDER",
        "宾语从句的语序",
        "英语",
        "ENG-CLAUSE",
    ),
    (
        "ENG-CLAUSE-ADVERBIAL-CONDITION",
        "条件状语从句",
        "英语",
        "ENG-CLAUSE",
    ),
    ("ENG-GRAMMAR-MODAL-MUST", "情态动词 must 的用法", "英语", "ENG-GRAMMAR"),
    (
        "ENG-GRAMMAR-AGREEMENT-PROXIMITY",
        "主谓一致的就近原则",
        "英语",
        "ENG-GRAMMAR",
    ),
    (
        "ENG-GRAMMAR-ADJECTIVE-COMPARATIVE",
        "形容词比较级",
        "英语",
        "ENG-GRAMMAR",
    ),
    ("ENG-READING-DETAIL", "细节理解", "英语", "ENG-READING"),
    ("ENG-READING-MAIN-IDEA", "主旨大意", "英语", "ENG-READING"),
    ("ENG-GRAMMAR-THERE-BE", "There be 句型", "英语", "ENG-GRAMMAR"),
    (
        "ENG-WRITING-SENTENCE-EXPRESSION",
        "基础句子表达",
        "英语",
        "ENG-WRITING",
    ),
]

# Incorrect labels from questions 41, 42, 48 and 60 are intentionally excluded.
ALIASES = [
    ("数学", "集合的交集", "MATH-SET-INTERSECTION"),
    ("数学", "函数定义域", "MATH-FUNCTION-DOMAIN"),
    ("数学", "函数单调性", "MATH-FUNCTION-MONOTONICITY"),
    ("数学", "函数奇偶性", "MATH-FUNCTION-PARITY"),
    ("数学", "特殊角三角函数值", "MATH-TRIG-SPECIAL-ANGLE"),
    ("数学", "同角三角函数关系", "MATH-TRIG-FUNDAMENTAL-IDENTITY"),
    ("数学", "向量坐标运算", "MATH-VECTOR-COORDINATE"),
    ("数学", "等差数列通项", "MATH-SEQUENCE-ARITHMETIC-GENERAL"),
    ("数学", "等比数列通项", "MATH-SEQUENCE-GEOMETRIC-GENERAL"),
    ("数学", "一元二次不等式", "MATH-INEQUALITY-QUADRATIC"),
    ("数学", "空间线面关系", "MATH-SOLID-LINE-PLANE-PERPENDICULAR"),
    ("数学", "直线斜率", "MATH-ANALYTIC-LINE-SLOPE"),
    ("数学", "复数运算", "MATH-COMPLEX-ARITHMETIC"),
    ("物理", "质点", "PHY-MOTION-PARTICLE-MODEL"),
    ("物理", "速度公式", "PHY-KINEMATICS-VELOCITY-EQUATION"),
    ("物理", "自由落体", "PHY-KINEMATICS-FREE-FALL"),
    ("物理", "平抛运动", "PHY-PROJECTILE-HORIZONTAL"),
    ("物理", "功", "PHY-WORK-ENERGY-WORK-CALCULATION"),
    ("物理", "动能", "PHY-WORK-ENERGY-KINETIC"),
    ("物理", "动量", "PHY-MOMENTUM-BASIC"),
    ("物理", "电功率", "PHY-CIRCUIT-ELECTRIC-POWER"),
    ("物理", "磁场方向", "PHY-MAGNETIC-FIELD-DIRECTION"),
    ("物理", "感应电流条件", "PHY-INDUCTION-CURRENT-CONDITION"),
    ("物理", "波速公式", "PHY-WAVE-SPEED-FREQUENCY-WAVELENGTH"),
    ("物理", "光的折射", "PHY-OPTICS-REFRACTION-PHENOMENON"),
    (
        "英语",
        "一般现在时的被动语态",
        "ENG-GRAMMAR-VOICE-PRESENT-PASSIVE",
    ),
    ("英语", "关系代词 that", "ENG-CLAUSE-RELATIVE-THAT"),
    ("英语", "关系副词 where", "ENG-CLAUSE-RELATIVE-WHERE"),
    ("英语", "宾语从句语序", "ENG-CLAUSE-OBJECT-WORD-ORDER"),
    ("英语", "情态动词 must", "ENG-GRAMMAR-MODAL-MUST"),
    ("英语", "就近原则", "ENG-GRAMMAR-AGREEMENT-PROXIMITY"),
    ("英语", "比较级", "ENG-GRAMMAR-ADJECTIVE-COMPARATIVE"),
    ("英语", "介词搭配", "ENG-VOCAB-COLLOCATION"),
    ("英语", "事实细节", "ENG-READING-DETAIL"),
    ("英语", "there be 句型", "ENG-GRAMMAR-THERE-BE"),
]


def _normalize_alias(value: str) -> str:
    return "".join(value.split()).casefold()


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


def _alias_table() -> sa.TableClause:
    return sa.table(
        "knowledge_point_aliases",
        sa.column("knowledge_point_id", sa.Integer()),
        sa.column("subject", sa.String()),
        sa.column("alias", sa.String()),
        sa.column("normalized_alias", sa.String()),
        sa.column("is_active", sa.Boolean()),
    )


def _code_rows(
    rows: list[tuple[str, str, str, str | None]],
    *,
    level: int,
    code_ids: dict[str, int],
) -> list[dict]:
    return [
        {
            "code": code,
            "name": name,
            "subject": subject,
            "parent_id": code_ids[parent_code] if parent_code else None,
            "level": level,
            "grade_scope": "高中",
            "sort_order": index,
            "is_active": True,
        }
        for index, (code, name, subject, parent_code) in enumerate(rows, start=1)
    ]


def _load_code_ids(bind: sa.Connection, table: sa.TableClause) -> dict[str, int]:
    return dict(bind.execute(sa.select(table.c.code, table.c.id)).all())


def _insert_points(
    bind: sa.Connection,
    table: sa.TableClause,
    rows: list[dict],
) -> None:
    if not rows:
        return
    bind.execute(
        postgresql.insert(table)
        .values(rows)
        .on_conflict_do_nothing(index_elements=["code"])
    )


def _validate_points(
    bind: sa.Connection,
    table: sa.TableClause,
    expected: list[dict],
) -> None:
    expected_by_code = {row["code"]: row for row in expected}
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
            ).where(table.c.code.in_(expected_by_code))
        )
    }
    missing = sorted(set(expected_by_code) - set(actual))
    if missing:
        raise RuntimeError(f"Missing knowledge-point codes after seed: {missing}")
    for code, expected_row in expected_by_code.items():
        row = actual[code]
        actual_values = (
            row.name,
            row.subject,
            row.parent_id,
            row.level,
            row.is_active,
        )
        expected_values = (
            expected_row["name"],
            expected_row["subject"],
            expected_row["parent_id"],
            expected_row["level"],
            True,
        )
        if actual_values != expected_values:
            raise RuntimeError(
                f"Knowledge-point code {code} already exists with conflicting data"
            )


def seed_catalog(bind: sa.Connection) -> None:
    points = _knowledge_table()
    aliases = _alias_table()
    code_ids: dict[str, int] = {}
    expected_rows: list[dict] = []

    for level, definitions in (
        (1, LEVEL_ONE),
        (2, LEVEL_TWO),
        (3, LEVEL_THREE),
    ):
        rows = _code_rows(definitions, level=level, code_ids=code_ids)
        _insert_points(bind, points, rows)
        code_ids = _load_code_ids(bind, points)
        _validate_points(bind, points, rows)
        expected_rows.extend(rows)

    alias_rows = [
        {
            "knowledge_point_id": code_ids[code],
            "subject": subject,
            "alias": alias,
            "normalized_alias": _normalize_alias(alias),
            "is_active": True,
        }
        for subject, alias, code in ALIASES
    ]
    bind.execute(
        postgresql.insert(aliases)
        .values(alias_rows)
        .on_conflict_do_nothing(index_elements=["subject", "normalized_alias"])
    )
    actual_aliases = {
        (row.subject, row.normalized_alias): row
        for row in bind.execute(
            sa.select(
                aliases.c.subject,
                aliases.c.normalized_alias,
                aliases.c.alias,
                aliases.c.knowledge_point_id,
                aliases.c.is_active,
            ).where(
                sa.tuple_(
                    aliases.c.subject,
                    aliases.c.normalized_alias,
                ).in_(
                    [
                        (row["subject"], row["normalized_alias"])
                        for row in alias_rows
                    ]
                )
            )
        )
    }
    for expected in alias_rows:
        key = (expected["subject"], expected["normalized_alias"])
        actual = actual_aliases.get(key)
        if not actual:
            raise RuntimeError(f"Missing knowledge-point alias after seed: {key}")
        if (
            actual.alias != expected["alias"]
            or actual.knowledge_point_id != expected["knowledge_point_id"]
            or not actual.is_active
        ):
            raise RuntimeError(f"Knowledge-point alias conflicts with seed data: {key}")

    if len({row["code"] for row in expected_rows}) != len(expected_rows):
        raise RuntimeError("Duplicate codes found in kp-mapping-v1 seed")


def upgrade() -> None:
    seed_catalog(op.get_bind())


def downgrade() -> None:
    bind = op.get_bind()
    points = _knowledge_table()
    aliases = _alias_table()
    all_codes = [code for code, _, _, _ in LEVEL_ONE + LEVEL_TWO + LEVEL_THREE]
    code_ids = _load_code_ids(bind, points)
    for subject, alias, code in ALIASES:
        knowledge_point_id = code_ids.get(code)
        if knowledge_point_id is not None:
            bind.execute(
                aliases.delete().where(
                    aliases.c.subject == subject,
                    aliases.c.normalized_alias == _normalize_alias(alias),
                    aliases.c.knowledge_point_id == knowledge_point_id,
                )
            )
    for definitions in (LEVEL_THREE, LEVEL_TWO, LEVEL_ONE):
        bind.execute(
            points.delete().where(
                points.c.code.in_([code for code, _, _, _ in definitions])
            )
        )
    remaining = bind.scalar(
        sa.select(sa.func.count()).select_from(points).where(points.c.code.in_(all_codes))
    )
    if remaining:
        raise RuntimeError("kp-mapping-v1 rollback left seeded knowledge points behind")
