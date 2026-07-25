from typing import Any

from app.models.knowledge_status import KnowledgeStatus
from app.models.student_answer import DifficultyFeedback, StudentAnswer
from app.services.student_answers import update_feedback


class FeedbackSession:
    def __init__(self, answer: StudentAnswer | None) -> None:
        self.answer = answer
        self.committed = False

    async def scalar(self, _query: object) -> Any:
        return self.answer

    async def commit(self) -> None:
        self.committed = True

    async def refresh(self, _value: object) -> None:
        pass


async def test_student_feedback_is_saved() -> None:
    answer = StudentAnswer(
        id=1,
        user_id=2,
        question_id=3,
        submitted_answer="A",
        is_correct=True,
    )
    db = FeedbackSession(answer)

    result = await update_feedback(db, 1, 2, DifficultyFeedback.difficult)  # type: ignore[arg-type]

    assert result is answer
    assert answer.difficulty_feedback == DifficultyFeedback.difficult
    assert db.committed


async def test_feedback_for_missing_or_foreign_answer_is_not_saved() -> None:
    db = FeedbackSession(None)

    result = await update_feedback(db, 99, 2, DifficultyFeedback.dont_know)  # type: ignore[arg-type]

    assert result is None
    assert not db.committed


def test_last_practiced_at_accepts_timezone_aware_values() -> None:
    column_type = KnowledgeStatus.__table__.c.last_practiced_at.type

    assert column_type.timezone is True
