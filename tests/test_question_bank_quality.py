import json
from types import SimpleNamespace

from app.cli.question_bank import SUPPORTED_SUBJECTS, build_parser
from app.models.question import QuestionType
from app.schemas.question_import import QuestionImportItem
from app.services.question_bank_quality import (
    _resolve_code,
    coverage_report,
    difficulty_report,
    lint_content,
    missing_report,
    verify_database,
)


def valid_question(**changes: object) -> dict:
    item = {
        "subject": "数学",
        "chapter": "函数",
        "knowledge_points": ["函数单调性"],
        "difficulty": 2,
        "type": "single_choice",
        "question": "函数 f(x)=2x+1 的单调性是？",
        "options": ["递增", "递减", "不确定"],
        "answer": "A",
        "solution": "斜率大于零，因此函数在定义域内单调递增。",
        "source": "测试题",
        "tags": ["kp:MATH-FUNCTION-MONOTONICITY"],
    }
    item.update(changes)
    return item


def test_lint_reuses_import_schema_and_fingerprint_duplicate_check() -> None:
    invalid = valid_question(question="", answer="D")
    content = json.dumps(
        [valid_question(), valid_question(), invalid],
        ensure_ascii=False,
    ).encode()

    report = lint_content(content, filename="math.json")

    assert report["total"] == 3
    assert report["passed"] == 1
    assert report["errors"] >= 2
    assert "重复" in report["items"][1]["errors"][0]


def test_lint_reports_warning_without_explicit_code() -> None:
    content = json.dumps(
        valid_question(tags=[]),
        ensure_ascii=False,
    ).encode()

    report = lint_content(content, filename="math.json")

    assert report["errors"] == 0
    assert report["warnings"] == 1
    assert "kp:<code>" in report["items"][0]["warnings"][0]


def test_resolve_code_accepts_active_code_and_applies_redirect() -> None:
    active = SimpleNamespace(
        id=1,
        code="MATH-SET-OPERATIONS",
        subject="数学",
        level=3,
        is_active=True,
    )
    catalog = {
        "by_code": {"MATH-SET-OPERATIONS": active},
        "by_name": {("数学", "集合的交集"): {"MATH-SET-INTERSECTION"}},
    }
    item = QuestionImportItem.model_validate(
        valid_question(
            chapter="集合",
            knowledge_points=["集合的交集"],
            tags=[],
        )
    )

    code, errors = _resolve_code(item, catalog)

    assert code == "MATH-SET-OPERATIONS"
    assert errors == []


def test_resolve_code_rejects_cross_subject_code() -> None:
    target = SimpleNamespace(
        id=1,
        code="PHY-MOTION-PARTICLE-MODEL",
        subject="物理",
        level=3,
        is_active=True,
    )
    catalog = {
        "by_code": {"PHY-MOTION-PARTICLE-MODEL": target},
        "by_name": {},
    }
    item = QuestionImportItem.model_validate(
        valid_question(tags=["kp:PHY-MOTION-PARTICLE-MODEL"])
    )

    code, errors = _resolve_code(item, catalog)

    assert code is None
    assert "学科不一致" in errors[0]


class FakeResult:
    def __init__(self, rows: list[object]) -> None:
        self._rows = rows

    def all(self) -> list[object]:
        return self._rows


class FakeSession:
    def __init__(self, result_sets: list[list[object]]) -> None:
        self._result_sets = iter(result_sets)

    async def execute(self, _statement: object) -> FakeResult:
        return FakeResult(next(self._result_sets))


def coverage_rows() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            code="MATH-FUNCTION-DOMAIN",
            name="函数的定义域",
            subject="数学",
            id=1,
            difficulty=2,
            question_type=QuestionType.single_choice,
        ),
        SimpleNamespace(
            code="MATH-FUNCTION-DOMAIN",
            name="函数的定义域",
            subject="数学",
            id=2,
            difficulty=3,
            question_type=QuestionType.single_choice,
        ),
        SimpleNamespace(
            code="MATH-FUNCTION-PARITY",
            name="函数的奇偶性",
            subject="数学",
            id=None,
            difficulty=None,
            question_type=None,
        ),
    ]


async def test_coverage_counts_primary_questions_and_empty_nodes() -> None:
    report = await coverage_report(FakeSession([coverage_rows()]))  # type: ignore[arg-type]

    assert report["knowledge_point_count"] == 2
    assert report["covered_count"] == 1
    assert report["question_count"] == 2
    assert report["items"][0]["difficulty_counts"]["2"] == 1


async def test_difficulty_aggregates_levels() -> None:
    report = await difficulty_report(FakeSession([coverage_rows()]))  # type: ignore[arg-type]

    assert report["question_count"] == 2
    assert report["average_difficulty"] == 2.5
    assert report["difficulty_counts"]["2"] == 1
    assert report["difficulty_counts"]["3"] == 1


async def test_missing_reports_empty_and_insufficient_nodes() -> None:
    report = await missing_report(
        FakeSession([coverage_rows()]),  # type: ignore[arg-type]
        minimum=5,
    )

    assert report["missing_count"] == 2
    assert report["empty_count"] == 1
    assert report["insufficient_count"] == 1
    assert {item["gap_to_minimum"] for item in report["items"]} == {3, 5}


async def test_verify_database_reports_missing_primary() -> None:
    rows = [
        SimpleNamespace(
            id=1,
            subject="数学",
            link_id=1,
            code="MATH-FUNCTION-DOMAIN",
            kp_subject="数学",
            level=3,
            is_active=True,
        ),
        SimpleNamespace(
            id=2,
            subject="数学",
            link_id=None,
            code=None,
            kp_subject=None,
            level=None,
            is_active=None,
        ),
    ]

    report = await verify_database(FakeSession([rows]))  # type: ignore[arg-type]

    assert report["active_question_count"] == 2
    assert report["valid_question_count"] == 1
    assert report["errors"] == 1
    assert report["issues"][0]["question_id"] == 2


def test_cli_exposes_all_phase_10_1_commands() -> None:
    parser = build_parser()
    assert parser.parse_args(["lint", "q.json"]).command == "lint"
    assert parser.parse_args(["coverage"]).command == "coverage"
    assert parser.parse_args(["difficulty"]).command == "difficulty"
    assert parser.parse_args(["missing"]).command == "missing"
    assert parser.parse_args(["verify"]).command == "verify"


def test_cli_accepts_qinghai_six_subjects() -> None:
    assert SUPPORTED_SUBJECTS == ["语文", "数学", "英语", "物理", "化学", "生物"]
    parser = build_parser()
    for subject in SUPPORTED_SUBJECTS:
        args = parser.parse_args(["coverage", "--subject", subject])
        assert args.subject == subject
