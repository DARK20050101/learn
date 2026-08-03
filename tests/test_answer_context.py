from typing import Any

import pytest
from fastapi import HTTPException

from app.models.knowledge_status import KnowledgeStatus
from app.models.question import Question, QuestionType
from app.models.student_answer import AnalysisStatus, StudentAnswer
from app.schemas.student_answer import AnswerSubmit
from app.services.student_answers import create_answer


class MissingDailyTaskSession:
    async def scalar(self, _query: object) -> Any:
        return None


async def test_daily_answer_rejects_foreign_or_mismatched_task_item() -> None:
    question = Question(
        id=1,
        title="测试题",
        content="1+1=?",
        subject="数学",
        question_type=QuestionType.single_choice,
        options=["1", "2"],
        correct_answer="2",
        explanation="基础计算",
        difficulty=1,
        knowledge_points=["基础"],
        tags=[],
        is_active=True,
    )
    payload = AnswerSubmit(
        question_id=question.id,
        daily_task_item_id=99,
        answer="2",
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_answer(MissingDailyTaskSession(), 7, question, payload)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 422
    assert "当前用户或题目不匹配" in exc_info.value.detail


class RecordingSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.committed = False

    async def scalar(self, _query: object) -> Any:
        return None

    def add(self, value: object) -> None:
        self.added.append(value)

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, _value: object) -> None:
        pass


def fill_blank_question() -> Question:
    return Question(
        id=1,
        title="概念",
        content="光合作用的场所是____。",
        subject="生物",
        question_type=QuestionType.fill_blank,
        correct_answer=["叶绿体", "叶绿体细胞"],
        explanation="光合作用发生在叶绿体中。",
        difficulty=2,
        knowledge_points=["光合作用"],
        tags=[],
        is_active=True,
    )


async def test_create_answer_fill_blank_correct_flow() -> None:
    db = RecordingSession()
    answer, created = await create_answer(
        db,
        7,
        fill_blank_question(),
        AnswerSubmit(question_id=1, answer="叶绿体。", duration_seconds=30),
    )
    assert created
    assert answer.is_correct
    assert answer.analysis_status == AnalysisStatus.not_requested
    assert db.committed
    assert any(isinstance(value, StudentAnswer) for value in db.added)
    assert any(isinstance(value, KnowledgeStatus) for value in db.added)


async def test_create_answer_fill_blank_accepts_synonym() -> None:
    db = RecordingSession()
    answer, _created = await create_answer(
        db,
        7,
        fill_blank_question(),
        AnswerSubmit(question_id=1, answer="叶绿体细胞", duration_seconds=20),
    )
    assert answer.is_correct


async def test_create_answer_fill_blank_wrong_marks_pending() -> None:
    db = RecordingSession()
    answer, _created = await create_answer(
        db,
        7,
        fill_blank_question(),
        AnswerSubmit(question_id=1, answer="细胞核", duration_seconds=15),
    )
    assert not answer.is_correct
    assert answer.analysis_status == AnalysisStatus.pending
