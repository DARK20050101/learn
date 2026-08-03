from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.models.question import Question, QuestionType
from app.models.training_session import TrainingType
from app.schemas.training_session import SubjectTrainingCreate
from app.services import fill_blank_training, subject_training
from app.services.subject_training import _matches, _target_difficulty


def make_question(
    *,
    subject: str = "数学",
    chapter: str = "函数",
    points: list[str] | None = None,
) -> Question:
    return Question(
        title="函数单调性",
        content="测试题",
        subject=subject,
        chapter=chapter,
        question_type=QuestionType.single_choice,
        options=["A", "B"],
        correct_answer="A",
        difficulty=3,
        knowledge_points=points or ["函数单调性"],
    )


def test_subject_training_request_limits_question_count() -> None:
    with pytest.raises(ValidationError):
        SubjectTrainingCreate(subject="数学", question_count=21)
    with pytest.raises(ValidationError):
        SubjectTrainingCreate(subject="数学", difficulty=6)


def test_subject_training_accepts_standard_code_and_difficulty() -> None:
    data = SubjectTrainingCreate(
        subject="数学",
        chapter="函数",
        knowledge_point_code="MATH-FUNCTION-DOMAIN",
        difficulty=2,
        question_count=5,
    )
    assert data.knowledge_point_code == "MATH-FUNCTION-DOMAIN"
    assert data.difficulty == 2


def test_subject_training_filter_matches_selected_scope() -> None:
    question = make_question()
    assert _matches(
        question,
        SubjectTrainingCreate(
            subject="数学",
            chapter="函数",
            knowledge_point="函数单调性",
            question_count=5,
        ),
    )
    assert not _matches(
        question,
        SubjectTrainingCreate(subject="物理", question_count=5),
    )
    assert not _matches(
        question,
        SubjectTrainingCreate(subject="数学", chapter="数列", question_count=5),
    )


def test_subject_training_difficulty_follows_mastery_and_recent_errors() -> None:
    assert _target_difficulty(20, False) == 2
    assert _target_difficulty(90, False) == 4
    assert _target_difficulty(90, True) == 2
    assert _target_difficulty(60, False) == 3


class ExecuteResult:
    def __init__(self, rows: list[tuple[Question, SimpleNamespace]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[Question, SimpleNamespace]]:
        return self._rows


class TrainingCreateSession:
    def __init__(self, rows: list[tuple[Question, SimpleNamespace]]) -> None:
        self._rows = rows

    async def execute(self, _statement: object) -> ExecuteResult:
        return ExecuteResult(self._rows)

    async def scalars(self, _statement: object) -> list[object]:
        return []


def fill_question(question_id: int) -> Question:
    return Question(
        id=question_id,
        title=f"概念{question_id}",
        content="光合作用的场所是____。",
        subject="生物",
        chapter="光合作用",
        question_type=QuestionType.fill_blank,
        correct_answer=["叶绿体"],
        difficulty=2,
        knowledge_points=["光合作用"],
        tags=[],
        is_active=True,
    )


def single_question(question_id: int) -> Question:
    return Question(
        id=question_id,
        title=f"题目{question_id}",
        content="测试题",
        subject="数学",
        chapter="函数",
        question_type=QuestionType.single_choice,
        options=["A", "B"],
        correct_answer="A",
        difficulty=2,
        knowledge_points=["函数单调性"],
        tags=[],
        is_active=True,
    )


def capture_session(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    captured: dict[str, object] = {}

    async def fake_create_session(
        db: object,
        user_id: int,
        *,
        training_type: TrainingType,
        title: str,
        selections: list[object],
        selection_version: str,
        selection_config: dict[str, object] | None = None,
        subject: str | None = None,
        chapter: str | None = None,
        knowledge_point: str | None = None,
    ) -> SimpleNamespace:
        captured.update(
            training_type=training_type,
            title=title,
            selection_version=selection_version,
            selection_config=selection_config,
            subject=subject,
            knowledge_point=knowledge_point,
        )
        return SimpleNamespace(id=99)

    monkeypatch.setattr(subject_training, "create_session", fake_create_session)
    return captured


async def test_create_fill_training_uses_fill_review_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        (fill_question(1), SimpleNamespace(id=1, name="光合作用")),
        (fill_question(2), SimpleNamespace(id=1, name="光合作用")),
    ]
    captured = capture_session(monkeypatch)

    await subject_training.create_subject_training(
        TrainingCreateSession(rows),  # type: ignore[arg-type]
        7,
        SubjectTrainingCreate(subject="生物", question_count=2),
        question_type=QuestionType.fill_blank,
    )

    assert captured["training_type"] == TrainingType.fill_review
    assert captured["title"] == "概念记忆 · 生物"
    assert captured["selection_version"] == "fill-v1"
    assert captured["selection_config"] is not None
    assert captured["selection_config"]["question_type"] == "fill_blank"


async def test_subject_training_keeps_subject_type_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [(single_question(1), SimpleNamespace(id=1, name="函数单调性"))]
    captured = capture_session(monkeypatch)

    await subject_training.create_subject_training(
        TrainingCreateSession(rows),  # type: ignore[arg-type]
        7,
        SubjectTrainingCreate(subject="数学", question_count=1),
    )

    assert captured["training_type"] == TrainingType.subject
    assert captured["selection_version"] == "subject-v2"
    assert captured["selection_config"] is not None
    assert captured["selection_config"]["question_type"] is None


async def test_fill_catalog_requests_fill_blank_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def fake_get_catalog(
        db: object,
        *,
        question_type: QuestionType | None = None,
    ) -> str:
        del db
        captured["question_type"] = question_type
        return "catalog"

    monkeypatch.setattr(subject_training, "get_catalog", fake_get_catalog)

    result = await fill_blank_training.get_fill_catalog(object())  # type: ignore[arg-type]

    assert result == "catalog"
    assert captured["question_type"] == QuestionType.fill_blank
