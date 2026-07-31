from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_task import DailyTask, DailyTaskItem
from app.models.knowledge_status import KnowledgeStatus
from app.models.question import Question, QuestionType
from app.models.student_answer import AnalysisStatus, DifficultyFeedback, StudentAnswer
from app.models.training_session import (
    TrainingSession,
    TrainingSessionItem,
    TrainingSessionStatus,
)
from app.schemas.question import AnswerValue
from app.schemas.student_answer import AnswerStats, AnswerSubmit


def evaluate_answer(question: Question, submitted: AnswerValue) -> bool:
    expected = question.correct_answer
    if question.question_type == QuestionType.multiple_choice:
        return (
            isinstance(submitted, list)
            and isinstance(expected, list)
            and {str(x).strip().casefold() for x in submitted}
            == {str(x).strip().casefold() for x in expected}
        )
    if question.question_type == QuestionType.true_false:
        return isinstance(submitted, bool) and submitted is expected
    return (
        isinstance(submitted, str)
        and isinstance(expected, str)
        and submitted.strip().casefold() == expected.strip().casefold()
    )


async def create_answer(
    db: AsyncSession, user_id: int, question: Question, data: AnswerSubmit
) -> tuple[StudentAnswer, bool]:
    if data.idempotency_key:
        existing = await db.scalar(
            select(StudentAnswer).where(
                StudentAnswer.user_id == user_id,
                StudentAnswer.idempotency_key == data.idempotency_key,
            )
        )
        if existing:
            if (
                existing.question_id != question.id
                or existing.daily_task_item_id != data.daily_task_item_id
                or existing.training_session_item_id != data.training_session_item_id
            ):
                raise HTTPException(409, "幂等键已经用于其他题目")
            return existing, False
    training_session: TrainingSession | None = None
    if data.daily_task_item_id is not None:
        daily_task = await db.scalar(
            select(DailyTask)
            .join(DailyTaskItem, DailyTaskItem.daily_task_id == DailyTask.id)
            .where(
                DailyTaskItem.id == data.daily_task_item_id,
                DailyTaskItem.question_id == question.id,
                DailyTask.user_id == user_id,
            )
            .with_for_update()
        )
        if not daily_task:
            raise HTTPException(422, "每日任务题目与当前用户或题目不匹配")
        existing_daily_answer = await db.scalar(
            select(StudentAnswer).where(
                StudentAnswer.user_id == user_id,
                StudentAnswer.daily_task_item_id == data.daily_task_item_id,
            )
        )
        if existing_daily_answer:
            raise HTTPException(409, "该每日任务题目已经提交过答案")
    if data.training_session_item_id is not None:
        training_session = await db.scalar(
            select(TrainingSession)
            .join(TrainingSessionItem, TrainingSessionItem.session_id == TrainingSession.id)
            .where(
                TrainingSessionItem.id == data.training_session_item_id,
                TrainingSessionItem.question_id == question.id,
                TrainingSession.user_id == user_id,
            )
            .with_for_update()
        )
        if not training_session:
            raise HTTPException(422, "训练题目与当前用户或题目不匹配")
        if training_session.status in {
            TrainingSessionStatus.completed,
            TrainingSessionStatus.cancelled,
        }:
            raise HTTPException(409, "该训练已经结束，不能继续提交答案")
    is_correct = evaluate_answer(question, data.answer)
    answer = StudentAnswer(
        user_id=user_id,
        question_id=question.id,
        daily_task_item_id=data.daily_task_item_id,
        training_session_item_id=data.training_session_item_id,
        submitted_answer=data.answer,
        is_correct=is_correct,
        duration_seconds=data.duration_seconds,
        idempotency_key=data.idempotency_key,
        analysis_status=(AnalysisStatus.not_requested if is_correct else AnalysisStatus.pending),
    )
    db.add(answer)
    if training_session and training_session.status == TrainingSessionStatus.pending:
        training_session.status = TrainingSessionStatus.in_progress
        training_session.started_at = datetime.now(UTC)
    await update_knowledge(db, user_id, question, answer.is_correct)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "答案重复提交或任务题目无效") from exc
    await db.refresh(answer)
    return answer, True


def recalculate_mastery(status: KnowledgeStatus) -> None:
    base_score = status.correct_count / status.attempt_count * 100 if status.attempt_count else 0
    ai_penalty = min((status.ai_gap_count or 0) * 5, 20)
    status.mastery_score = round(max(0, base_score - ai_penalty), 2)


async def update_knowledge(
    db: AsyncSession, user_id: int, question: Question, correct: bool
) -> None:
    subject = question.subject
    point = question.knowledge_points[0] if question.knowledge_points else question.title
    status = await db.scalar(
        select(KnowledgeStatus)
        .where(
            KnowledgeStatus.user_id == user_id,
            KnowledgeStatus.subject == subject,
            KnowledgeStatus.knowledge_point == point,
        )
        .with_for_update()
    )
    if not status:
        status = KnowledgeStatus(
            user_id=user_id,
            subject=subject,
            knowledge_point=point,
            attempt_count=0,
            correct_count=0,
            ai_gap_count=0,
            mastery_score=0,
        )
        db.add(status)
    status.attempt_count += 1
    status.correct_count += int(correct)
    recalculate_mastery(status)
    status.last_practiced_at = datetime.now(UTC)


async def update_feedback(
    db: AsyncSession,
    answer_id: int,
    user_id: int,
    feedback: DifficultyFeedback,
) -> StudentAnswer | None:
    answer = await db.scalar(
        select(StudentAnswer).where(
            StudentAnswer.id == answer_id,
            StudentAnswer.user_id == user_id,
        )
    )
    if not answer:
        return None
    answer.difficulty_feedback = feedback
    await db.commit()
    await db.refresh(answer)
    return answer


async def list_answers(
    db: AsyncSession, user_id: int, page: int, page_size: int
) -> tuple[list[StudentAnswer], int]:
    total = (
        await db.scalar(
            select(func.count(StudentAnswer.id)).where(StudentAnswer.user_id == user_id)
        )
        or 0
    )
    rows = await db.scalars(
        select(StudentAnswer)
        .where(StudentAnswer.user_id == user_id)
        .order_by(StudentAnswer.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(rows), total


async def list_task_answers(
    db: AsyncSession, user_id: int, task_id: int
) -> list[tuple[StudentAnswer, Question]]:
    rows = await db.execute(
        select(StudentAnswer, Question)
        .join(Question, Question.id == StudentAnswer.question_id)
        .join(DailyTaskItem, DailyTaskItem.id == StudentAnswer.daily_task_item_id)
        .where(
            StudentAnswer.user_id == user_id,
            DailyTaskItem.daily_task_id == task_id,
            StudentAnswer.question_id == DailyTaskItem.question_id,
        )
        .order_by(DailyTaskItem.position)
    )
    return list(rows.all())


async def get_stats(db: AsyncSession, user_id: int) -> AnswerStats:
    total, correct = (
        await db.execute(
            select(
                func.count(StudentAnswer.id),
                func.sum(case((StudentAnswer.is_correct.is_(True), 1), else_=0)),
            ).where(StudentAnswer.user_id == user_id)
        )
    ).one()
    total, correct = int(total or 0), int(correct or 0)
    return AnswerStats(
        total=total, correct=correct, accuracy=round(correct / total, 4) if total else 0
    )
