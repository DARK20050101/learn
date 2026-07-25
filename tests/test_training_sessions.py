from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.training_session import (
    TrainingSession,
    TrainingSessionStatus,
    TrainingType,
)
from app.schemas.student_answer import AnswerSubmit
from app.services.training_sessions import (
    TrainingItemSelection,
    complete_session,
    create_session,
)


class CompletionSession:
    def __init__(self, session: TrainingSession, answered_count: int) -> None:
        self.session = session
        self.answered_count = answered_count
        self.scalar_calls = 0
        self.committed = False

    async def scalar(self, _query: object) -> Any:
        self.scalar_calls += 1
        if self.scalar_calls == 2:
            return self.answered_count
        return self.session

    async def commit(self) -> None:
        self.committed = True


def make_session(status: TrainingSessionStatus = TrainingSessionStatus.pending) -> TrainingSession:
    session = TrainingSession(
        id=12,
        user_id=3,
        training_type=TrainingType.subject,
        title="数学专项",
        status=status,
        total_questions=6,
        selection_version="subject-v1",
        selection_config={},
    )
    session.items = []
    return session


def test_answer_cannot_belong_to_daily_and_generic_training() -> None:
    with pytest.raises(ValidationError):
        AnswerSubmit(
            question_id=1,
            daily_task_item_id=2,
            training_session_item_id=3,
            answer="A",
        )


async def test_duplicate_questions_are_rejected_before_session_creation() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await create_session(
            object(),  # type: ignore[arg-type]
            1,
            training_type=TrainingType.subject,
            title="英语专项",
            selections=[TrainingItemSelection(1), TrainingItemSelection(1)],
            selection_version="subject-v1",
        )

    assert exc_info.value.status_code == 422
    assert "重复题目" in str(exc_info.value.detail)


async def test_incomplete_generic_session_cannot_complete() -> None:
    session = make_session()
    db = CompletionSession(session, answered_count=4)

    with pytest.raises(HTTPException) as exc_info:
        await complete_session(db, user_id=3, session_id=12)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 409
    assert "4/6" in str(exc_info.value.detail)
    assert session.status == TrainingSessionStatus.pending
    assert not db.committed


async def test_all_answers_complete_generic_session() -> None:
    session = make_session()
    db = CompletionSession(session, answered_count=6)

    result = await complete_session(db, user_id=3, session_id=12)  # type: ignore[arg-type]

    assert result.status == TrainingSessionStatus.completed
    assert result.completed_at is not None
    assert db.committed


async def test_repeated_generic_completion_is_idempotent() -> None:
    session = make_session(TrainingSessionStatus.completed)
    session.completed_at = datetime.now(UTC)
    db = CompletionSession(session, answered_count=6)

    result = await complete_session(db, user_id=3, session_id=12)  # type: ignore[arg-type]

    assert result is session
    assert not db.committed


def test_completed_question_count_is_not_a_persisted_session_column() -> None:
    assert "completed_questions" not in TrainingSession.__table__.c
