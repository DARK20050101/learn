from typing import Any

import pytest
from fastapi import HTTPException

from app.models.question import Question, QuestionType
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
