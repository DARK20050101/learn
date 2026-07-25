from enum import StrEnum

from pydantic import BaseModel, Field

from app.models.student_answer import AnalysisStatus
from app.schemas.question import AnswerValue


class MistakeType(StrEnum):
    concept = "概念理解错误"
    calculation = "计算错误"
    reading = "审题错误"
    method = "方法选择错误"
    memory = "知识记忆错误"
    other = "其他"


class AIAnalysisInput(BaseModel):
    question: str = Field(min_length=1, max_length=10000)
    student_answer: AnswerValue
    correct_answer: AnswerValue
    knowledge_points: list[str] = Field(min_length=1)
    standard_solution: str | None = Field(default=None, max_length=10000)


class AIAnalysisResult(BaseModel):
    mistake_type: MistakeType
    reason: str = Field(min_length=1, max_length=1000)
    knowledge_gap: str = Field(min_length=1, max_length=100)
    suggestion: str = Field(min_length=1, max_length=1000)
    next_training: str = Field(min_length=1, max_length=500)


class AnalysisResponseStatus(StrEnum):
    not_required = "not_required"
    pending = AnalysisStatus.pending.value
    completed = AnalysisStatus.completed.value
    failed = AnalysisStatus.failed.value


class AIAnalysisResponse(BaseModel):
    answer_id: int
    status: AnalysisResponseStatus
    analysis: AIAnalysisResult | None = None
