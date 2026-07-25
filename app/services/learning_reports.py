from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_point import KnowledgePoint
from app.models.knowledge_status import KnowledgeStatus
from app.models.student_answer import StudentAnswer
from app.schemas.learning_report import (
    LearningReportRead,
    LearningReportRecommendation,
    LearningReportSummary,
    LearningReportTrendDay,
    LearningReportWeakPoint,
)
from app.services.daily_task_generator import CHINA_TIMEZONE

REPORT_TIMEZONE = "Asia/Shanghai"
TREND_DAYS = 7


def _summary(results: list[bool]) -> LearningReportSummary:
    correct = sum(results)
    total = len(results)
    return LearningReportSummary(
        completed=total,
        correct=correct,
        accuracy=round(correct / total, 4) if total else 0,
    )


def _as_china_date(value: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(CHINA_TIMEZONE).date()


def build_report(
    *,
    now: datetime,
    answers: list[tuple[datetime, bool]],
    weak_rows: list[tuple[KnowledgeStatus, str | None, str | None]],
) -> LearningReportRead:
    china_now = now.astimezone(CHINA_TIMEZONE)
    today = china_now.date()
    week_start = today - timedelta(days=today.weekday())
    trend_start = today - timedelta(days=TREND_DAYS - 1)

    by_date: dict[date, list[bool]] = {}
    for created_at, is_correct in answers:
        answer_date = _as_china_date(created_at)
        by_date.setdefault(answer_date, []).append(is_correct)

    today_summary = _summary(by_date.get(today, []))
    week_results = [
        result
        for answer_date, results in by_date.items()
        if week_start <= answer_date <= today
        for result in results
    ]
    trend = [
        LearningReportTrendDay(
            date=day,
            **_summary(by_date.get(day, [])).model_dump(),
        )
        for day in (trend_start + timedelta(days=index) for index in range(TREND_DAYS))
    ]
    weak_points = [
        LearningReportWeakPoint(
            subject=status.subject,
            knowledge_point_code=code,
            knowledge_point_name=standard_name or status.knowledge_point,
            mastery_score=round(status.mastery_score, 2),
            attempt_count=status.attempt_count,
            error_count=max(status.attempt_count - status.correct_count, 0),
        )
        for status, code, standard_name in weak_rows
    ]
    if weak_points:
        weakest = weak_points[0]
        recommendation = LearningReportRecommendation(
            subject=weakest.subject,
            knowledge_point_code=weakest.knowledge_point_code,
            knowledge_point_name=weakest.knowledge_point_name,
            message=f"建议优先练习{weakest.subject}·{weakest.knowledge_point_name}，先巩固基础题。",
        )
    else:
        recommendation = LearningReportRecommendation(
            subject=None,
            knowledge_point_code=None,
            knowledge_point_name=None,
            message="先完成今日6题，系统会根据作答逐步发现你的薄弱知识点。",
        )

    return LearningReportRead(
        generated_at=now,
        timezone=REPORT_TIMEZONE,
        today=today_summary,
        week=_summary(week_results),
        recent_trend=trend,
        weak_points=weak_points,
        recommendation=recommendation,
    )


async def get_report(db: AsyncSession, user_id: int) -> LearningReportRead:
    now = datetime.now(UTC)
    china_today = now.astimezone(CHINA_TIMEZONE).date()
    trend_start = china_today - timedelta(days=TREND_DAYS - 1)
    cutoff = datetime.combine(trend_start, time.min, tzinfo=CHINA_TIMEZONE).astimezone(UTC)

    answer_rows = list(
        (
            await db.execute(
                select(StudentAnswer.created_at, StudentAnswer.is_correct)
                .where(
                    StudentAnswer.user_id == user_id,
                    StudentAnswer.created_at >= cutoff,
                )
                .order_by(StudentAnswer.created_at)
            )
        ).all()
    )
    weak_rows = list(
        (
            await db.execute(
                select(KnowledgeStatus, KnowledgePoint.code, KnowledgePoint.name)
                .outerjoin(
                    KnowledgePoint,
                    KnowledgePoint.id == KnowledgeStatus.knowledge_point_id,
                )
                .where(
                    KnowledgeStatus.user_id == user_id,
                    KnowledgeStatus.attempt_count > 0,
                )
                .order_by(
                    KnowledgeStatus.mastery_score,
                    KnowledgeStatus.attempt_count.desc(),
                    KnowledgeStatus.id,
                )
                .limit(3)
            )
        ).all()
    )
    return build_report(now=now, answers=answer_rows, weak_rows=weak_rows)
