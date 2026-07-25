from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.training_session import TrainingSessionStatus, TrainingType
from app.schemas.question import AnswerValue, QuestionRead


class TrainingSessionItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    recommendation_reason: str | None
    source_answer_id: int | None
    question: QuestionRead


class TrainingSessionRead(BaseModel):
    id: int
    training_type: TrainingType
    title: str
    status: TrainingSessionStatus
    total_questions: int
    completed_questions: int
    subject: str | None
    chapter: str | None
    knowledge_point: str | None
    scheduled_date: date | None
    plan_day: int | None
    selection_version: str
    selection_config: dict
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    items: list[TrainingSessionItemRead]


class TrainingSessionSummary(BaseModel):
    id: int
    training_type: TrainingType
    title: str
    status: TrainingSessionStatus
    total_questions: int
    completed_questions: int
    subject: str | None
    created_at: datetime
    completed_at: datetime | None


class TrainingAnswerSubmit(BaseModel):
    answer: AnswerValue
    duration_seconds: int | None = Field(None, ge=0, le=86400)
    idempotency_key: str = Field(min_length=1, max_length=64)


class SubjectTrainingCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=50)
    chapter: str | None = Field(default=None, min_length=1, max_length=100)
    knowledge_point: str | None = Field(default=None, min_length=1, max_length=100)
    knowledge_point_code: str | None = Field(default=None, min_length=1, max_length=100)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    question_count: int = Field(default=10, ge=1, le=20)


class SubjectTrainingKnowledgePoint(BaseModel):
    code: str
    name: str
    question_count: int
    difficulty_counts: dict[int, int]


class SubjectTrainingChapter(BaseModel):
    name: str
    question_count: int
    difficulty_counts: dict[int, int]
    knowledge_points: list[SubjectTrainingKnowledgePoint]


class SubjectTrainingSubject(BaseModel):
    name: str
    question_count: int
    difficulty_counts: dict[int, int]
    chapters: list[SubjectTrainingChapter]


class SubjectTrainingCatalog(BaseModel):
    subjects: list[SubjectTrainingSubject]
