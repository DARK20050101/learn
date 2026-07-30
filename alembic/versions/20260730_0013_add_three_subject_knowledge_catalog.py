"""Add MVP knowledge catalogs for Chinese, chemistry, and biology."""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260730_0013"
down_revision: str | None = "20260726_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ROOTS = [
    ("CHN", "语文", "语文", 40),
    ("CHEM", "化学", "化学", 50),
    ("BIO", "生物", "生物", 60),
]

MODULES = [
    ("CHN-LANGUAGE", "语言文字运用", "语文", "CHN", 10),
    ("CHN-MODERN-READING", "现代文阅读", "语文", "CHN", 20),
    ("CHN-CLASSICAL", "文言文阅读", "语文", "CHN", 30),
    ("CHN-POETRY", "古代诗歌阅读", "语文", "CHN", 40),
    ("CHN-MEMORIZATION", "名篇名句默写", "语文", "CHN", 50),
    ("CHN-WRITING", "写作", "语文", "CHN", 60),
    ("CHEM-CONCEPT", "化学基本概念", "化学", "CHEM", 10),
    ("CHEM-INORGANIC", "无机元素及其化合物", "化学", "CHEM", 20),
    ("CHEM-REACTION", "化学反应原理", "化学", "CHEM", 30),
    ("CHEM-ORGANIC", "有机化学基础", "化学", "CHEM", 40),
    ("CHEM-EXPERIMENT", "化学实验", "化学", "CHEM", 50),
    ("CHEM-STRUCTURE", "物质结构与性质", "化学", "CHEM", 60),
    ("BIO-CELL", "分子与细胞", "生物", "BIO", 10),
    ("BIO-METABOLISM", "细胞代谢", "生物", "BIO", 20),
    ("BIO-GENETICS", "遗传与进化", "生物", "BIO", 30),
    ("BIO-HOMEOSTASIS", "稳态与调节", "生物", "BIO", 40),
    ("BIO-ECOLOGY", "生物与环境", "生物", "BIO", 50),
    ("BIO-TECHNOLOGY", "生物技术与实验", "生物", "BIO", 60),
]

POINTS = [
    ("CHN-LANGUAGE-WORDS", "词语辨析与使用", "语文", "CHN-LANGUAGE", 10),
    ("CHN-LANGUAGE-SENTENCE", "病句辨析与修改", "语文", "CHN-LANGUAGE", 20),
    ("CHN-LANGUAGE-EXPRESSION", "语言表达与衔接", "语文", "CHN-LANGUAGE", 30),
    ("CHN-MODERN-INFORMATION", "信息筛选与整合", "语文", "CHN-MODERN-READING", 10),
    ("CHN-MODERN-INFERENCE", "文意理解与推断", "语文", "CHN-MODERN-READING", 20),
    ("CHN-MODERN-APPRECIATION", "表现手法与文本鉴赏", "语文", "CHN-MODERN-READING", 30),
    ("CHN-CLASSICAL-WORDS", "文言实词与虚词", "语文", "CHN-CLASSICAL", 10),
    ("CHN-CLASSICAL-TRANSLATION", "文言文翻译", "语文", "CHN-CLASSICAL", 20),
    ("CHN-CLASSICAL-CONTENT", "文言文内容理解", "语文", "CHN-CLASSICAL", 30),
    ("CHN-POETRY-IMAGE", "诗歌形象与意境", "语文", "CHN-POETRY", 10),
    ("CHN-POETRY-EMOTION", "诗歌思想感情", "语文", "CHN-POETRY", 20),
    ("CHN-POETRY-TECHNIQUE", "诗歌表达技巧", "语文", "CHN-POETRY", 30),
    ("CHN-MEMORIZATION-CONTEXT", "理解性默写", "语文", "CHN-MEMORIZATION", 10),
    ("CHN-MEMORIZATION-VARIANTS", "易错字与通假字", "语文", "CHN-MEMORIZATION", 20),
    ("CHN-MEMORIZATION-AUTHOR", "篇目作者与语境", "语文", "CHN-MEMORIZATION", 30),
    ("CHN-WRITING-ARGUMENT", "议论文立意", "语文", "CHN-WRITING", 10),
    ("CHN-WRITING-STRUCTURE", "论证结构与方法", "语文", "CHN-WRITING", 20),
    ("CHN-WRITING-MATERIAL", "材料分析与运用", "语文", "CHN-WRITING", 30),
    ("CHEM-CONCEPT-AMOUNT", "物质的量与化学计量", "化学", "CHEM-CONCEPT", 10),
    ("CHEM-CONCEPT-ION", "离子反应与离子方程式", "化学", "CHEM-CONCEPT", 20),
    ("CHEM-CONCEPT-REDOX", "氧化还原反应", "化学", "CHEM-CONCEPT", 30),
    ("CHEM-INORGANIC-METAL", "金属及其化合物", "化学", "CHEM-INORGANIC", 10),
    ("CHEM-INORGANIC-NONMETAL", "非金属及其化合物", "化学", "CHEM-INORGANIC", 20),
    ("CHEM-INORGANIC-TRANSFORMATION", "无机物转化与推断", "化学", "CHEM-INORGANIC", 30),
    ("CHEM-REACTION-ENERGY", "化学反应与能量", "化学", "CHEM-REACTION", 10),
    ("CHEM-REACTION-RATE-EQUILIBRIUM", "反应速率与化学平衡", "化学", "CHEM-REACTION", 20),
    ("CHEM-REACTION-AQUEOUS", "水溶液中的离子平衡", "化学", "CHEM-REACTION", 30),
    ("CHEM-ORGANIC-STRUCTURE", "有机物结构与性质", "化学", "CHEM-ORGANIC", 10),
    ("CHEM-ORGANIC-REACTION", "有机反应类型", "化学", "CHEM-ORGANIC", 20),
    ("CHEM-ORGANIC-SYNTHESIS", "有机合成与推断", "化学", "CHEM-ORGANIC", 30),
    ("CHEM-EXPERIMENT-OPERATION", "实验基本操作与安全", "化学", "CHEM-EXPERIMENT", 10),
    ("CHEM-EXPERIMENT-DESIGN", "实验方案设计与评价", "化学", "CHEM-EXPERIMENT", 20),
    ("CHEM-EXPERIMENT-ANALYSIS", "实验现象与数据分析", "化学", "CHEM-EXPERIMENT", 30),
    ("CHEM-STRUCTURE-ATOM", "原子结构与元素周期律", "化学", "CHEM-STRUCTURE", 10),
    ("CHEM-STRUCTURE-BOND", "化学键与分子结构", "化学", "CHEM-STRUCTURE", 20),
    ("CHEM-STRUCTURE-CRYSTAL", "晶体结构与性质", "化学", "CHEM-STRUCTURE", 30),
    ("BIO-CELL-MOLECULE", "组成细胞的分子", "生物", "BIO-CELL", 10),
    ("BIO-CELL-STRUCTURE", "细胞结构与功能", "生物", "BIO-CELL", 20),
    ("BIO-CELL-LIFE-CYCLE", "细胞生命历程", "生物", "BIO-CELL", 30),
    ("BIO-METABOLISM-ENZYME-ATP", "酶与ATP", "生物", "BIO-METABOLISM", 10),
    ("BIO-METABOLISM-RESPIRATION", "细胞呼吸", "生物", "BIO-METABOLISM", 20),
    ("BIO-METABOLISM-PHOTOSYNTHESIS", "光合作用", "生物", "BIO-METABOLISM", 30),
    ("BIO-GENETICS-LAWS", "遗传基本规律", "生物", "BIO-GENETICS", 10),
    ("BIO-GENETICS-MOLECULAR", "遗传的分子基础", "生物", "BIO-GENETICS", 20),
    ("BIO-GENETICS-VARIATION-EVOLUTION", "变异、育种与进化", "生物", "BIO-GENETICS", 30),
    ("BIO-HOMEOSTASIS-NEURAL-HUMORAL", "神经调节与体液调节", "生物", "BIO-HOMEOSTASIS", 10),
    ("BIO-HOMEOSTASIS-IMMUNE", "免疫调节", "生物", "BIO-HOMEOSTASIS", 20),
    ("BIO-HOMEOSTASIS-PLANT", "植物生命活动调节", "生物", "BIO-HOMEOSTASIS", 30),
    ("BIO-ECOLOGY-POPULATION-COMMUNITY", "种群与群落", "生物", "BIO-ECOLOGY", 10),
    ("BIO-ECOLOGY-ECOSYSTEM", "生态系统结构与功能", "生物", "BIO-ECOLOGY", 20),
    ("BIO-ECOLOGY-ENVIRONMENT", "生态环境保护", "生物", "BIO-ECOLOGY", 30),
    ("BIO-TECHNOLOGY-EXPERIMENT", "教材基础实验", "生物", "BIO-TECHNOLOGY", 10),
    ("BIO-TECHNOLOGY-FERMENTATION", "发酵工程", "生物", "BIO-TECHNOLOGY", 20),
    ("BIO-TECHNOLOGY-CELL-GENE", "细胞工程与基因工程", "生物", "BIO-TECHNOLOGY", 30),
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


def _seed_level(
    bind: sa.Connection,
    rows: list[tuple],
    *,
    level: int,
) -> None:
    table = _table()
    parent_codes = {row[3] for row in rows if level > 1}
    parents = {}
    if parent_codes:
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
            raise RuntimeError(f"Missing catalog parents: {sorted(parent_codes - set(parents))}")

    expected = []
    for row in rows:
        code, name, subject = row[:3]
        parent_code = row[3] if level > 1 else None
        sort_order = row[4] if level > 1 else row[3]
        parent = parents.get(parent_code)
        if parent and (
            parent.subject != subject
            or parent.level != level - 1
            or not parent.is_active
        ):
            raise RuntimeError(f"Invalid parent {parent_code} for {code}")
        expected.append(
            {
                "code": code,
                "name": name,
                "subject": subject,
                "parent_id": parent.id if parent else None,
                "level": level,
                "grade_scope": "高中",
                "sort_order": sort_order,
                "is_active": True,
            }
        )

    bind.execute(
        postgresql.insert(table)
        .values(expected)
        .on_conflict_do_nothing(index_elements=["code"])
    )
    actual = {
        row.code: dict(row._mapping)
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
            ).where(table.c.code.in_([item["code"] for item in expected]))
        )
    }
    for item in expected:
        if actual.get(item["code"]) != item:
            raise RuntimeError(f"Knowledge-point code {item['code']} conflicts with catalog")


def upgrade() -> None:
    bind = op.get_bind()
    _seed_level(bind, ROOTS, level=1)
    _seed_level(bind, MODULES, level=2)
    _seed_level(bind, POINTS, level=3)


def downgrade() -> None:
    table = _table()
    bind = op.get_bind()
    for rows in (POINTS, MODULES, ROOTS):
        bind.execute(table.delete().where(table.c.code.in_([row[0] for row in rows])))
