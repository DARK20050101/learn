from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.daily_task import DailyTask, DailyTaskItem, DailyTaskStatus
from app.models.question import Question
from app.models.student_answer import StudentAnswer
from app.schemas.daily_task import DailyTaskCreate
from app.services.daily_task_generator import CHINA_TIMEZONE, daily_task_generator


async def create_task(db: AsyncSession, user_id: int, data: DailyTaskCreate) -> DailyTask:
    if len(set(data.question_ids)) != 6:
        raise HTTPException(422, "每日任务必须包含 6 道不同题目")
    existing = await db.scalar(
        select(DailyTask).where(DailyTask.user_id == user_id, DailyTask.task_date == data.task_date)
    )
    if existing:
        return await get_task(db, user_id, existing.id)
    questions = list(
        await db.scalars(
            select(Question).where(Question.id.in_(data.question_ids), Question.is_active.is_(True))
        )
    )
    if len(questions) != 6:
        raise HTTPException(422, "题目不存在、已停用或数量不足 6 道")
    task = DailyTask(user_id=user_id, task_date=data.task_date, day_number=data.day_number)
    by_id = {q.id: q for q in questions}
    task.items = [
        DailyTaskItem(position=i, question=by_id[qid], recommendation_reason="MVP 手动选题")
        for i, qid in enumerate(data.question_ids, 1)
    ]
    db.add(task)
    await db.commit()
    return await get_task(db, user_id, task.id)


async def get_task(db: AsyncSession, user_id: int, task_id: int) -> DailyTask:
    task = await db.scalar(
        select(DailyTask)
        .where(DailyTask.id == task_id, DailyTask.user_id == user_id)
        .options(selectinload(DailyTask.items).selectinload(DailyTaskItem.question))
    )
    if not task:
        raise HTTPException(404, "每日任务不存在")
    return task


async def get_today(db: AsyncSession, user_id: int) -> DailyTask:
    return await daily_task_generator.get_or_create_today(db, user_id)


async def refresh_today(db: AsyncSession, user_id: int) -> DailyTask:
    task = await db.scalar(
        select(DailyTask)
        .where(
            DailyTask.user_id == user_id,
            DailyTask.task_date == datetime.now(CHINA_TIMEZONE).date(),
        )
        .options(selectinload(DailyTask.items).selectinload(DailyTaskItem.question))
        .with_for_update()
    )
    if not task:
        task = await daily_task_generator.get_or_create_today(db, user_id)
        task = await db.scalar(
            select(DailyTask)
            .where(DailyTask.id == task.id)
            .options(selectinload(DailyTask.items).selectinload(DailyTaskItem.question))
            .with_for_update()
        )
    if not task:
        raise HTTPException(404, "今日任务不存在")
    if task.refresh_count >= 1:
        raise HTTPException(409, "今天的刷新次数已经用完")
    if task.status == DailyTaskStatus.completed:
        raise HTTPException(409, "今日任务已经完成，不能刷新")

    item_ids = [item.id for item in task.items]
    answered_count = 0
    if item_ids:
        answered_count = (
            await db.scalar(
                select(func.count(StudentAnswer.id)).where(
                    StudentAnswer.user_id == user_id,
                    StudentAnswer.daily_task_item_id.in_(item_ids),
                )
            )
            or 0
        )
    if answered_count:
        raise HTTPException(409, "今日训练已经开始，不能刷新题目")

    old_question_ids = {item.question_id for item in task.items}
    recommendations = await daily_task_generator.recommend_today(
        db,
        user_id,
        additionally_excluded_question_ids=old_question_ids,
    )
    task.items.clear()
    await db.flush()
    task.items = [
        DailyTaskItem(
            position=position,
            question=recommendation.question,
            recommendation_reason=recommendation.reason,
        )
        for position, recommendation in enumerate(recommendations, start=1)
    ]
    task.version = 2
    task.refresh_count = 1
    task.refreshed_at = datetime.now(UTC)
    await db.commit()
    return await get_task(db, user_id, task.id)


async def complete_task(db: AsyncSession, user_id: int, task_id: int) -> DailyTask:
    task = await get_task(db, user_id, task_id)
    item_ids = {item.id for item in task.items}
    if len(item_ids) != 6:
        raise HTTPException(409, "今日任务题目不足，暂时无法完成")
    answered_count = (
        await db.scalar(
            select(func.count(func.distinct(StudentAnswer.daily_task_item_id)))
            .join(DailyTaskItem, DailyTaskItem.id == StudentAnswer.daily_task_item_id)
            .where(
                StudentAnswer.user_id == user_id,
                StudentAnswer.daily_task_item_id.in_(item_ids),
                StudentAnswer.question_id == DailyTaskItem.question_id,
            )
        )
        or 0
    )
    if answered_count != 6:
        raise HTTPException(409, f"今日任务尚未完成：已完成 {answered_count}/6 题")
    if task.status == DailyTaskStatus.completed:
        return task
    task.status = DailyTaskStatus.completed
    task.completed_at = datetime.now(UTC)
    await db.commit()
    return await get_task(db, user_id, task_id)
