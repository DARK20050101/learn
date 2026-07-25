from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.student_answer import AnalysisStatus, DifficultyFeedback
from app.schemas.question import AnswerValue


class AnswerSubmit(BaseModel):
    question_id: int
    daily_task_item_id: int | None = None
    training_session_item_id: int | None = None
    answer: AnswerValue
    duration_seconds: int | None = Field(None, ge=0, le=86400)
    idempotency_key: str | None = Field(None, max_length=64)

    @model_validator(mode="after")
    def validate_training_context(self) -> "AnswerSubmit":
        if self.daily_task_item_id is not None and self.training_session_item_id is not None:
            raise ValueError("一次答题只能属于一种训练上下文")
        return self


class StudentAnswerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    question_id: int
    daily_task_item_id: int | None
    training_session_item_id: int | None
    submitted_answer: AnswerValue
    is_correct: bool
    analysis_status: AnalysisStatus
    ai_analysis: dict | None
    difficulty_feedback: DifficultyFeedback | None
    created_at: datetime


class AnswerResult(StudentAnswerRead):
    correct_answer: AnswerValue
    explanation: str | None


class AnswerStats(BaseModel):
    total: int
    correct: int
    accuracy: float


class AnswerFeedbackUpdate(BaseModel):
    difficulty_feedback: DifficultyFeedback


class AnswerFeedbackRead(BaseModel):
    answer_id: int
    difficulty_feedback: DifficultyFeedback
