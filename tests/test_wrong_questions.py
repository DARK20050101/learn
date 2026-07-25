from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.models.question import Question, QuestionType
from app.models.student_answer import AnalysisStatus, StudentAnswer
from app.models.training_session import TrainingSession, TrainingType
from app.schemas.wrong_question import WrongQuestionSort
from app.services import wrong_questions
from app.services.wrong_questions import (
    build_wrong_questions_query,
    create_wrong_review,
    list_wrong_questions,
)


def test_wrong_question_query_is_user_scoped_and_supports_filters() -> None:
    statement = build_wrong_questions_query(
        42,
        subject="数学",
        knowledge_point_code="MATH-FUNCTION-DOMAIN",
    )
    compiled = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )
    assert "student_answers.user_id = 42" in compiled
    assert "student_answers.is_correct IS false" in compiled
    assert "questions.subject = '数学'" in compiled
    assert "knowledge_points.code = 'MATH-FUNCTION-DOMAIN'" in compiled
    assert "row_number() OVER" in compiled
    assert "count(student_answers.id) OVER" in compiled


class FakeMappings:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)


class FakeResult:
    def __init__(self, rows: list[dict]) -> None:
        self.rows = rows

    def mappings(self) -> FakeMappings:
        return FakeMappings(self.rows)


class FakeSession:
    def __init__(self, rows: list[dict], total: int) -> None:
        self.rows = rows
        self.total = total
        self.executed = []

    async def scalar(self, statement):
        self.executed.append(statement)
        return self.total

    async def execute(self, statement):
        self.executed.append(statement)
        return FakeResult(self.rows)


async def test_wrong_question_rows_use_latest_error_and_count() -> None:
    row = {
        "answer_id": 9,
        "question_id": 3,
        "title": "函数定义域",
        "content": "求函数定义域。",
        "question_type": QuestionType.single_choice,
        "options": ["A", "B"],
        "subject": "数学",
        "chapter": "函数",
        "knowledge_point_code": "MATH-FUNCTION-DOMAIN",
        "knowledge_point_name": "函数的定义域",
        "difficulty": 2,
        "submitted_answer": "A",
        "correct_answer": "B",
        "explanation": "先检查根式和分母。",
        "analysis_status": AnalysisStatus.failed,
        "ai_analysis": None,
        "last_wrong_at": datetime(2026, 7, 25, tzinfo=UTC),
        "error_count": 3,
    }
    db = FakeSession([row], total=1)
    items, total = await list_wrong_questions(
        db, 7,
        subject=None,
        knowledge_point_code=None,
        sort=WrongQuestionSort.error_count_desc,
        page=1,
        page_size=20,
    )
    assert total == 1
    assert len(items) == 1
    assert items[0].answer_id == 9
    assert items[0].error_count == 3
    assert items[0].analysis_status == AnalysisStatus.failed


async def test_wrong_question_empty_state_is_stable() -> None:
    items, total = await list_wrong_questions(
        FakeSession([], total=0),
        7,
        subject="英语",
        knowledge_point_code=None,
        sort=WrongQuestionSort.recent_desc,
        page=2,
        page_size=10,
    )
    assert items == []
    assert total == 0


class ScalarSequenceSession:
    def __init__(self, values: list[object | None]) -> None:
        self.values = iter(values)

    async def scalar(self, _statement):
        return next(self.values)


async def test_wrong_review_rejects_question_not_owned_by_user() -> None:
    with pytest.raises(HTTPException, match="不在你的错题本"):
        await create_wrong_review(ScalarSequenceSession([None]), 7, 3)  # type: ignore[arg-type]


async def test_wrong_review_reuses_training_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answer = StudentAnswer(
        id=9,
        user_id=7,
        question_id=3,
        submitted_answer="A",
        is_correct=False,
    )
    question = Question(
        id=3,
        title="函数定义域",
        content="求定义域",
        subject="数学",
        chapter="函数",
        question_type=QuestionType.single_choice,
        options=["A", "B"],
        correct_answer="B",
        difficulty=2,
        knowledge_points=["函数的定义域"],
        tags=[],
        is_active=True,
    )
    expected = TrainingSession(
        id=11,
        user_id=7,
        training_type=TrainingType.wrong_review,
        title="错题重练",
        total_questions=1,
        selection_version="wrong-review-v1",
    )
    captured = {}

    async def fake_create_session(_db, user_id, **kwargs):
        captured["user_id"] = user_id
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(wrong_questions, "create_session", fake_create_session)
    result = await create_wrong_review(
        ScalarSequenceSession([answer, question]), 7, 3  # type: ignore[arg-type]
    )
    assert result is expected
    assert captured["training_type"] == TrainingType.wrong_review
    assert captured["selections"][0].question_id == 3
    assert captured["selections"][0].source_answer_id == 9
