from datetime import UTC, date, datetime
from typing import Any

import pytest
from fastapi import HTTPException

from app.models.daily_task import DailyTask, DailyTaskItem, DailyTaskStatus
from app.models.question import Question, QuestionType
from app.models.student_answer import AnalysisStatus, StudentAnswer
from app.services.daily_tasks import complete_task
from app.services.student_answers import list_task_answers


def make_task(status: DailyTaskStatus = DailyTaskStatus.pending) -> DailyTask:
    task = DailyTask(id=10, user_id=1, task_date=date.today(), day_number=1, status=status)
    task.items = [
        DailyTaskItem(id=index, daily_task_id=10, question_id=index, position=index)
        for index in range(1, 7)
    ]
    return task


class CompletionSession:
    def __init__(self, task: DailyTask, answered_count: int) -> None:
        self.task = task
        self.answered_count = answered_count
        self.scalar_calls = 0
        self.committed = False

    async def scalar(self, _query: object) -> Any:
        self.scalar_calls += 1
        if self.scalar_calls == 2:
            return self.answered_count
        return self.task

    async def commit(self) -> None:
        self.committed = True


async def test_incomplete_task_cannot_be_marked_completed() -> None:
    task = make_task()
    db = CompletionSession(task, answered_count=4)

    with pytest.raises(HTTPException) as exc_info:
        await complete_task(db, user_id=1, task_id=task.id)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 409
    assert "4/6" in str(exc_info.value.detail)
    assert task.status == DailyTaskStatus.pending
    assert not db.committed


async def test_all_six_answers_complete_task() -> None:
    task = make_task()
    db = CompletionSession(task, answered_count=6)

    result = await complete_task(db, user_id=1, task_id=task.id)  # type: ignore[arg-type]

    assert result.status == DailyTaskStatus.completed
    assert result.completed_at is not None
    assert db.committed


async def test_repeated_completion_is_idempotent() -> None:
    task = make_task(DailyTaskStatus.completed)
    task.completed_at = datetime.now(UTC)
    db = CompletionSession(task, answered_count=6)

    result = await complete_task(db, user_id=1, task_id=task.id)  # type: ignore[arg-type]

    assert result is task
    assert not db.committed


class ResultRows:
    def __init__(self, rows: list[tuple[StudentAnswer, Question]]) -> None:
        self._rows = rows

    def all(self) -> list[tuple[StudentAnswer, Question]]:
        return self._rows


class RecoverySession:
    def __init__(self, rows: list[tuple[StudentAnswer, Question]]) -> None:
        self.rows = rows

    async def execute(self, _query: object) -> ResultRows:
        return ResultRows(self.rows)


async def test_task_answer_recovery_keeps_result_and_analysis_state() -> None:
    question = Question(
        id=3,
        title="函数单调性",
        content="测试题",
        subject="数学",
        question_type=QuestionType.single_choice,
        options=["A", "B"],
        correct_answer="A",
        explanation="标准解析",
        difficulty=2,
        knowledge_points=["函数单调性"],
        tags=[],
    )
    answer = StudentAnswer(
        id=8,
        user_id=1,
        question_id=3,
        daily_task_item_id=4,
        submitted_answer="B",
        is_correct=False,
        analysis_status=AnalysisStatus.completed,
        ai_analysis={"mistake_type": "概念理解错误"},
    )
    db = RecoverySession([(answer, question)])

    rows = await list_task_answers(db, user_id=1, task_id=10)  # type: ignore[arg-type]

    assert rows == [(answer, question)]
    assert rows[0][0].submitted_answer == "B"
    assert rows[0][0].analysis_status == AnalysisStatus.completed
    assert rows[0][1].correct_answer == "A"
    assert rows[0][1].explanation == "标准解析"
