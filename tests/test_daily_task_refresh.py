from datetime import date
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.models.daily_task import DailyTask, DailyTaskItem, DailyTaskStatus
from app.models.question import Question, QuestionType
from app.services.daily_task_generator import Recommendation
from app.services.daily_tasks import refresh_today


def make_question(question_id: int, subject: str) -> Question:
    return Question(
        id=question_id,
        title=f"{subject}-{question_id}",
        content=f"题目 {question_id}",
        subject=subject,
        chapter="测试",
        question_type=QuestionType.single_choice,
        options=["A", "B"],
        correct_answer="A",
        explanation="解析",
        difficulty=2,
        knowledge_points=["基础"],
        tags=[],
        is_active=True,
    )


def make_refreshable_task(*, refresh_count: int = 0) -> DailyTask:
    task = DailyTask(
        id=10,
        user_id=1,
        task_date=date.today(),
        day_number=1,
        status=DailyTaskStatus.pending,
        version=refresh_count + 1,
        refresh_count=refresh_count,
    )
    task.items = [
        DailyTaskItem(
            id=index,
            daily_task_id=10,
            question_id=index,
            position=index,
            question=make_question(index, "英语"),
        )
        for index in range(1, 7)
    ]
    return task


class RefreshSession:
    def __init__(self, task: DailyTask, answered_count: int = 0) -> None:
        self.task = task
        self.answered_count = answered_count
        self.scalar_calls = 0
        self.flushed = False
        self.committed = False

    async def scalar(self, _query: object):
        self.scalar_calls += 1
        if self.scalar_calls == 2:
            return self.answered_count
        return self.task

    async def flush(self) -> None:
        self.flushed = True

    async def commit(self) -> None:
        self.committed = True


async def test_refresh_replaces_unanswered_items_once(monkeypatch: pytest.MonkeyPatch) -> None:
    task = make_refreshable_task()
    db = RefreshSession(task)
    new_questions = [make_question(index, "英语") for index in range(7, 13)]
    recommend = AsyncMock(
        return_value=[
            Recommendation(question=question, reason="刷新推荐") for question in new_questions
        ]
    )
    monkeypatch.setattr(
        "app.services.daily_tasks.daily_task_generator.recommend_today",
        recommend,
    )

    result = await refresh_today(db, user_id=1)  # type: ignore[arg-type]

    assert result is task
    assert [item.question.id for item in result.items] == list(range(7, 13))
    assert result.version == 2
    assert result.refresh_count == 1
    assert result.refreshed_at is not None
    assert db.flushed
    assert db.committed
    recommend.assert_awaited_once()
    assert recommend.await_args.kwargs["additionally_excluded_question_ids"] == set(range(1, 7))


async def test_second_refresh_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    task = make_refreshable_task(refresh_count=1)
    db = RefreshSession(task)
    recommend = AsyncMock()
    monkeypatch.setattr(
        "app.services.daily_tasks.daily_task_generator.recommend_today",
        recommend,
    )

    with pytest.raises(HTTPException) as exc_info:
        await refresh_today(db, user_id=1)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 409
    assert "次数" in str(exc_info.value.detail)
    recommend.assert_not_awaited()
    assert not db.committed


async def test_started_task_cannot_be_refreshed(monkeypatch: pytest.MonkeyPatch) -> None:
    task = make_refreshable_task()
    db = RefreshSession(task, answered_count=1)
    recommend = AsyncMock()
    monkeypatch.setattr(
        "app.services.daily_tasks.daily_task_generator.recommend_today",
        recommend,
    )

    with pytest.raises(HTTPException) as exc_info:
        await refresh_today(db, user_id=1)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 409
    assert "已经开始" in str(exc_info.value.detail)
    recommend.assert_not_awaited()
    assert not db.committed


def test_refresh_migration_is_reversible() -> None:
    source = (
        Path(__file__).parents[1]
        / "alembic"
        / "versions"
        / "20260725_0011_daily_task_refresh.py"
    ).read_text(encoding="utf-8")

    assert 'revision: str = "20260725_0011"' in source
    assert 'down_revision: str | None = "20260723_0010"' in source
    assert source.count("op.add_column(") == 3
    assert source.count("op.drop_column(") == 3
    assert "ck_daily_task_refresh_version" in source
