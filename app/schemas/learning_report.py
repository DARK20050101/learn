from datetime import date, datetime

from pydantic import BaseModel


class LearningReportSummary(BaseModel):
    completed: int
    correct: int
    accuracy: float


class LearningReportTrendDay(LearningReportSummary):
    date: date


class LearningReportWeakPoint(BaseModel):
    subject: str
    knowledge_point_code: str | None
    knowledge_point_name: str
    mastery_score: float
    attempt_count: int
    error_count: int


class LearningReportRecommendation(BaseModel):
    subject: str | None
    knowledge_point_code: str | None
    knowledge_point_name: str | None
    message: str


class LearningReportRead(BaseModel):
    generated_at: datetime
    timezone: str
    today: LearningReportSummary
    week: LearningReportSummary
    recent_trend: list[LearningReportTrendDay]
    weak_points: list[LearningReportWeakPoint]
    recommendation: LearningReportRecommendation
