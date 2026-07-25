from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel

from app.models.question import QuestionType
from app.models.student_answer import AnalysisStatus
from app.schemas.ai_analysis import AIAnalysisResult
from app.schemas.question import AnswerValue


class WrongQuestionSort(StrEnum):
    error_count_desc = "error_count_desc"
    recent_desc = "recent_desc"


class WrongQuestionRead(BaseModel):
    answer_id: int
    question_id: int
    title: str
    content: str
    question_type: QuestionType
    options: list[str] | None
    subject: str
    chapter: str | None
    knowledge_point_code: str
    knowledge_point_name: str
    difficulty: int
    submitted_answer: AnswerValue
    correct_answer: AnswerValue
    explanation: str | None
    analysis_status: AnalysisStatus
    ai_analysis: AIAnalysisResult | None
    last_wrong_at: datetime
    error_count: int
