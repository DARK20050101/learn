from datetime import UTC, datetime

from app.models.knowledge_status import KnowledgeStatus
from app.services.learning_reports import build_report


def test_report_uses_beijing_date_boundaries_and_calendar_week() -> None:
    now = datetime(2026, 7, 25, 1, 0, tzinfo=UTC)  # 北京时间周六 09:00
    report = build_report(
        now=now,
        answers=[
            (datetime(2026, 7, 24, 15, 59, tzinfo=UTC), False),  # 北京时间周五
            (datetime(2026, 7, 24, 16, 1, tzinfo=UTC), True),  # 北京时间周六
            (datetime(2026, 7, 25, 0, 30, tzinfo=UTC), False),  # 北京时间周六
        ],
        weak_rows=[],
    )

    assert report.today.completed == 2
    assert report.today.correct == 1
    assert report.today.accuracy == 0.5
    assert report.week.completed == 3
    assert report.week.correct == 1
    assert report.timezone == "Asia/Shanghai"
    assert len(report.recent_trend) == 7
    assert report.recent_trend[-1].date.isoformat() == "2026-07-25"


def test_report_returns_top_weak_point_and_rule_based_recommendation() -> None:
    status = KnowledgeStatus(
        subject="数学",
        knowledge_point="函数单调性",
        mastery_score=35,
        attempt_count=5,
        correct_count=2,
        ai_gap_count=1,
    )

    report = build_report(
        now=datetime(2026, 7, 25, tzinfo=UTC),
        answers=[],
        weak_rows=[
            (
                status,
                "MATH-FUNCTION-MONOTONICITY",
                "函数单调性",
            )
        ],
    )

    assert report.weak_points[0].error_count == 3
    assert report.weak_points[0].knowledge_point_code == "MATH-FUNCTION-MONOTONICITY"
    assert report.recommendation.subject == "数学"
    assert "函数单调性" in report.recommendation.message


def test_empty_report_has_actionable_onboarding_message() -> None:
    report = build_report(
        now=datetime(2026, 7, 25, tzinfo=UTC),
        answers=[],
        weak_rows=[],
    )

    assert report.today.completed == 0
    assert report.week.completed == 0
    assert report.weak_points == []
    assert "今日6题" in report.recommendation.message
