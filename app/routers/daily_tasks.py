from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.daily_task import DailyTaskCreate, DailyTaskRead
from app.schemas.student_answer import AnswerResult, StudentAnswerRead
from app.services import daily_tasks as service
from app.services import student_answers

router = APIRouter(prefix="/daily-tasks", tags=["每日任务"])


@router.post("", response_model=DailyTaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(data: DailyTaskCreate, db: DbSession, user: CurrentUser) -> DailyTaskRead:
    return await service.create_task(db, user.id, data)


@router.get("/today", response_model=DailyTaskRead)
async def today(db: DbSession, user: CurrentUser) -> DailyTaskRead:
    return await service.get_today(db, user.id)


@router.post("/today/refresh", response_model=DailyTaskRead)
async def refresh_today(db: DbSession, user: CurrentUser) -> DailyTaskRead:
    return await service.refresh_today(db, user.id)


@router.get("/{task_id}", response_model=DailyTaskRead)
async def get_task(task_id: int, db: DbSession, user: CurrentUser) -> DailyTaskRead:
    return await service.get_task(db, user.id, task_id)


@router.get("/{task_id}/answers", response_model=list[AnswerResult])
async def task_answers(task_id: int, db: DbSession, user: CurrentUser) -> list[AnswerResult]:
    await service.get_task(db, user.id, task_id)
    rows = await student_answers.list_task_answers(db, user.id, task_id)
    return [
        AnswerResult(
            **StudentAnswerRead.model_validate(answer).model_dump(),
            correct_answer=question.correct_answer,
            explanation=question.explanation,
        )
        for answer, question in rows
    ]


@router.post("/{task_id}/complete", response_model=DailyTaskRead)
async def complete(task_id: int, db: DbSession, user: CurrentUser) -> DailyTaskRead:
    return await service.complete_task(db, user.id, task_id)
