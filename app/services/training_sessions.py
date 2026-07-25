from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question import Question
from app.models.student_answer import StudentAnswer
from app.models.training_session import (
    TrainingSession,
    TrainingSessionItem,
    TrainingSessionStatus,
    TrainingType,
)
from app.schemas.student_answer import AnswerSubmit
from app.schemas.training_session import TrainingAnswerSubmit
from app.services.student_answers import create_answer


@dataclass(frozen=True)
class TrainingItemSelection:
    question_id: int
    recommendation_reason: str | None = None
    source_answer_id: int | None = None


async def create_session(
    db: AsyncSession,
    user_id: int,
    *,
    training_type: TrainingType,
    title: str,
    selections: list[TrainingItemSelection],
    selection_version: str,
    selection_config: dict | None = None,
    subject: str | None = None,
    chapter: str | None = None,
    knowledge_point: str | None = None,
) -> TrainingSession:
    if not 1 <= len(selections) <= 100:
        raise HTTPException(422, "训练题量必须在 1 到 100 之间")
    question_ids = [selection.question_id for selection in selections]
    if len(set(question_ids)) != len(question_ids):
        raise HTTPException(422, "同一次训练不能包含重复题目")
    questions = list(
        await db.scalars(
            select(Question).where(Question.id.in_(question_ids), Question.is_active.is_(True))
        )
    )
    if len(questions) != len(question_ids):
        raise HTTPException(422, "部分题目不存在或已经停用")
    by_id = {question.id: question for question in questions}
    session = TrainingSession(
        user_id=user_id,
        training_type=training_type,
        title=title,
        total_questions=len(selections),
        subject=subject,
        chapter=chapter,
        knowledge_point=knowledge_point,
        selection_version=selection_version,
        selection_config=selection_config or {},
        items=[
            TrainingSessionItem(
                position=position,
                question=by_id[selection.question_id],
                recommendation_reason=selection.recommendation_reason,
                source_answer_id=selection.source_answer_id,
            )
            for position, selection in enumerate(selections, start=1)
        ],
    )
    db.add(session)
    await db.commit()
    return await get_session(db, user_id, session.id)


async def get_session(db: AsyncSession, user_id: int, session_id: int) -> TrainingSession:
    session = await db.scalar(
        select(TrainingSession)
        .where(TrainingSession.id == session_id, TrainingSession.user_id == user_id)
        .options(
            selectinload(TrainingSession.items).selectinload(TrainingSessionItem.question)
        )
    )
    if not session:
        raise HTTPException(404, "训练不存在")
    return session


async def get_item(
    db: AsyncSession, user_id: int, item_id: int
) -> tuple[TrainingSessionItem, TrainingSession]:
    row = (
        await db.execute(
            select(TrainingSessionItem, TrainingSession)
            .join(TrainingSession, TrainingSession.id == TrainingSessionItem.session_id)
            .where(
                TrainingSessionItem.id == item_id,
                TrainingSession.user_id == user_id,
            )
            .options(selectinload(TrainingSessionItem.question))
        )
    ).one_or_none()
    if not row:
        raise HTTPException(404, "训练题目不存在")
    return row


async def completed_count(db: AsyncSession, user_id: int, session_id: int) -> int:
    return int(
        await db.scalar(
            select(func.count(func.distinct(StudentAnswer.training_session_item_id)))
            .join(
                TrainingSessionItem,
                TrainingSessionItem.id == StudentAnswer.training_session_item_id,
            )
            .where(
                StudentAnswer.user_id == user_id,
                TrainingSessionItem.session_id == session_id,
                StudentAnswer.question_id == TrainingSessionItem.question_id,
            )
        )
        or 0
    )


async def completed_counts(
    db: AsyncSession, user_id: int, session_ids: list[int]
) -> dict[int, int]:
    if not session_ids:
        return {}
    rows = (
        await db.execute(
            select(
                TrainingSessionItem.session_id,
                func.count(func.distinct(StudentAnswer.training_session_item_id)),
            )
            .join(
                StudentAnswer,
                StudentAnswer.training_session_item_id == TrainingSessionItem.id,
            )
            .join(TrainingSession, TrainingSession.id == TrainingSessionItem.session_id)
            .where(
                TrainingSession.user_id == user_id,
                TrainingSessionItem.session_id.in_(session_ids),
                StudentAnswer.user_id == user_id,
                StudentAnswer.question_id == TrainingSessionItem.question_id,
            )
            .group_by(TrainingSessionItem.session_id)
        )
    ).all()
    return {session_id: int(count) for session_id, count in rows}


async def list_sessions(
    db: AsyncSession, user_id: int, page: int, page_size: int
) -> tuple[list[TrainingSession], int]:
    total = (
        await db.scalar(
            select(func.count(TrainingSession.id)).where(TrainingSession.user_id == user_id)
        )
        or 0
    )
    sessions = list(
        await db.scalars(
            select(TrainingSession)
            .where(TrainingSession.user_id == user_id)
            .order_by(TrainingSession.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return sessions, int(total)


async def list_session_answers(
    db: AsyncSession, user_id: int, session_id: int
) -> list[tuple[StudentAnswer, Question]]:
    await get_session(db, user_id, session_id)
    rows = await db.execute(
        select(StudentAnswer, Question)
        .join(Question, Question.id == StudentAnswer.question_id)
        .join(
            TrainingSessionItem,
            TrainingSessionItem.id == StudentAnswer.training_session_item_id,
        )
        .where(
            StudentAnswer.user_id == user_id,
            TrainingSessionItem.session_id == session_id,
            StudentAnswer.question_id == TrainingSessionItem.question_id,
        )
        .order_by(TrainingSessionItem.position)
    )
    return list(rows.all())


async def submit_item_answer(
    db: AsyncSession,
    user_id: int,
    item_id: int,
    data: TrainingAnswerSubmit,
) -> tuple[StudentAnswer, Question, bool]:
    item, session = await get_item(db, user_id, item_id)
    if session.status in {TrainingSessionStatus.completed, TrainingSessionStatus.cancelled}:
        raise HTTPException(409, "该训练已经结束，不能继续提交答案")
    answer, created = await create_answer(
        db,
        user_id,
        item.question,
        AnswerSubmit(
            question_id=item.question_id,
            training_session_item_id=item.id,
            answer=data.answer,
            duration_seconds=data.duration_seconds,
            idempotency_key=data.idempotency_key,
        ),
    )
    return answer, item.question, created


async def complete_session(
    db: AsyncSession, user_id: int, session_id: int
) -> TrainingSession:
    session = await get_session(db, user_id, session_id)
    count = await completed_count(db, user_id, session_id)
    if count != session.total_questions:
        raise HTTPException(
            409,
            f"本次训练尚未完成：已完成 {count}/{session.total_questions} 题",
        )
    if session.status == TrainingSessionStatus.completed:
        return session
    session.status = TrainingSessionStatus.completed
    session.completed_at = datetime.now(UTC)
    await db.commit()
    return await get_session(db, user_id, session_id)
