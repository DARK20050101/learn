from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.daily_task import DailyTaskStatus
from app.schemas.question import QuestionRead


class DailyTaskCreate(BaseModel):
    task_date: date
    day_number: int = Field(ge=1, le=27)
    question_ids: list[int] = Field(min_length=6, max_length=6)


class DailyTaskItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    position: int
    recommendation_reason: str | None
    question: QuestionRead


class DailyTaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_date: date
    day_number: int
    status: DailyTaskStatus
    completed_at: datetime | None
    version: int
    refresh_count: int
    refreshed_at: datetime | None
    items: list[DailyTaskItemRead]
