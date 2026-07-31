from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.daily_task import DailyTask, DailyTaskItem
from app.models.knowledge_status import KnowledgeStatus
from app.models.question import Question
from app.models.student_answer import StudentAnswer

SUBJECT_PRIORITY = ("英语", "物理", "数学", "化学", "生物")
DEFAULT_SUBJECT_QUOTAS = {"英语": 3, "物理": 2, "数学": 1}
QUESTIONS_PER_DAY = 6
RECENT_EXCLUSION_DAYS = 7
CHINA_TIMEZONE = timezone(timedelta(hours=8), "Asia/Shanghai")


@dataclass(frozen=True)
class SubjectPerformance:
    error_rate: float | None = None
    consecutive_correct: int = 0

    @property
    def preferred_difficulties(self) -> tuple[int, int]:
        if self.error_rate is not None and self.error_rate >= 0.5:
            return (1, 2)
        if self.consecutive_correct >= 3:
            return (3, 4)
        return (2, 3)


@dataclass(frozen=True)
class Recommendation:
    question: Question
    reason: str


def _material_group(question: Question) -> str | None:
    prefix = "material-group:"
    return next(
        (tag[len(prefix) :] for tag in question.tags if tag.startswith(prefix)),
        None,
    )


def _question_mastery(question: Question, mastery_scores: dict[tuple[str, str], float]) -> float:
    scores = [
        mastery_scores[(question.subject, point)]
        for point in question.knowledge_points
        if (question.subject, point) in mastery_scores
    ]
    return min(scores) if scores else 50.0


def _rank_subject_questions(
    questions: list[Question],
    performance: SubjectPerformance,
    mastery_scores: dict[tuple[str, str], float],
    recent_wrong_points: set[tuple[str, str]],
) -> list[Question]:
    low, high = performance.preferred_difficulties
    target = (low + high) / 2

    def score(question: Question) -> tuple[float, float, int]:
        mastery = _question_mastery(question, mastery_scores)
        wrong_point_bonus = (
            20
            if any(
                (question.subject, point) in recent_wrong_points
                for point in question.knowledge_points
            )
            else 0
        )
        difficulty_penalty = abs(question.difficulty - target) * 12
        return (mastery - wrong_point_bonus + difficulty_penalty, mastery, question.id or 0)

    return sorted(questions, key=score)


def choose_questions(
    candidates: list[Question],
    performances: dict[str, SubjectPerformance],
    mastery_scores: dict[tuple[str, str], float],
    recent_wrong_points: set[tuple[str, str]],
    quotas: dict[str, int] | None = None,
) -> list[Recommendation]:
    """Choose six unique questions using deterministic, explainable rules."""
    quotas = quotas or DEFAULT_SUBJECT_QUOTAS
    by_subject: dict[str, list[Question]] = defaultdict(list)
    for question in candidates:
        by_subject[question.subject].append(question)
    ranked = {
        subject: _rank_subject_questions(
            questions,
            performances.get(subject, SubjectPerformance()),
            mastery_scores,
            recent_wrong_points,
        )
        for subject, questions in by_subject.items()
    }

    selected: list[Recommendation] = []
    selected_ids: set[int] = set()
    selected_material_groups: set[str] = set()

    def can_take(question: Question, *, allow_repeated_group: bool = False) -> bool:
        if question.id in selected_ids:
            return False
        group = _material_group(question)
        return allow_repeated_group or group is None or group not in selected_material_groups

    def append(question: Question, reason: str) -> None:
        selected.append(Recommendation(question=question, reason=reason))
        selected_ids.add(question.id)
        group = _material_group(question)
        if group:
            selected_material_groups.add(group)

    def take(subject: str, count: int, reason_prefix: str) -> None:
        for question in ranked.get(subject, []):
            if len([item for item in selected if item.question.subject == subject]) >= count:
                break
            if not can_take(question):
                continue
            performance = performances.get(subject, SubjectPerformance())
            low, high = performance.preferred_difficulties
            points = "、".join(question.knowledge_points[:2]) or "基础知识"
            append(
                question,
                f"{reason_prefix}；{points}；适配难度 {low}-{high}",
            )

    for subject in SUBJECT_PRIORITY:
        if subject in quotas:
            take(subject, quotas[subject], f"{subject}学科优先训练")

    if len(selected) < QUESTIONS_PER_DAY:
        fallback_subjects = list(SUBJECT_PRIORITY) + sorted(
            subject for subject in ranked if subject not in SUBJECT_PRIORITY
        )
        for subject in fallback_subjects:
            for question in ranked.get(subject, []):
                if len(selected) >= QUESTIONS_PER_DAY:
                    break
                if not can_take(question):
                    continue
                append(question, f"{subject}题库补位；避免当日重复材料")
            if len(selected) >= QUESTIONS_PER_DAY:
                break

    # A very small bank may only have multiple questions from the same material.
    # Keep the task available in that exceptional case, while preferring one item
    # per material group whenever the bank has enough variety.
    if len(selected) < QUESTIONS_PER_DAY:
        for subject in list(SUBJECT_PRIORITY) + sorted(
            subject for subject in ranked if subject not in SUBJECT_PRIORITY
        ):
            for question in ranked.get(subject, []):
                if len(selected) >= QUESTIONS_PER_DAY:
                    break
                if not can_take(question, allow_repeated_group=True):
                    continue
                append(question, f"{subject}题库补位；材料组题量有限")
            if len(selected) >= QUESTIONS_PER_DAY:
                break

    return selected[:QUESTIONS_PER_DAY]


def _build_performances(
    rows: list[tuple[str, bool, list[str]]],
) -> tuple[dict[str, SubjectPerformance], set[tuple[str, str]]]:
    by_subject: dict[str, list[bool]] = defaultdict(list)
    recent_wrong_points: set[tuple[str, str]] = set()
    for subject, is_correct, knowledge_points in rows:
        by_subject[subject].append(is_correct)
        if not is_correct:
            recent_wrong_points.update((subject, point) for point in knowledge_points)

    performances: dict[str, SubjectPerformance] = {}
    for subject, results in by_subject.items():
        consecutive_correct = 0
        for is_correct in results:
            if not is_correct:
                break
            consecutive_correct += 1
        performances[subject] = SubjectPerformance(
            error_rate=sum(not value for value in results) / len(results),
            consecutive_correct=consecutive_correct,
        )
    return performances, recent_wrong_points


class DailyTaskGenerator:
    async def recommend_today(
        self,
        db: AsyncSession,
        user_id: int,
        *,
        additionally_excluded_question_ids: set[int] | None = None,
    ) -> list[Recommendation]:
        recent_cutoff = datetime.now(UTC) - timedelta(days=RECENT_EXCLUSION_DAYS)
        recent_question_ids = set(
            await db.scalars(
                select(StudentAnswer.question_id)
                .where(
                    StudentAnswer.user_id == user_id,
                    StudentAnswer.created_at >= recent_cutoff,
                )
                .distinct()
            )
        )
        recent_question_ids.update(additionally_excluded_question_ids or set())
        candidate_query = select(Question).where(Question.is_active.is_(True))
        if recent_question_ids:
            candidate_query = candidate_query.where(Question.id.not_in(recent_question_ids))
        candidates = list(await db.scalars(candidate_query.order_by(Question.id)))

        knowledge_rows = list(
            await db.scalars(select(KnowledgeStatus).where(KnowledgeStatus.user_id == user_id))
        )
        mastery_scores = {
            (row.subject, row.knowledge_point): row.mastery_score for row in knowledge_rows
        }
        history_rows = (
            await db.execute(
                select(Question.subject, StudentAnswer.is_correct, Question.knowledge_points)
                .join(StudentAnswer, StudentAnswer.question_id == Question.id)
                .where(StudentAnswer.user_id == user_id)
                .order_by(StudentAnswer.created_at.desc())
                .limit(50)
            )
        ).all()
        performances, recent_wrong_points = _build_performances(list(history_rows))
        recommendations = choose_questions(
            candidates,
            performances,
            mastery_scores,
            recent_wrong_points,
        )
        if len(recommendations) < QUESTIONS_PER_DAY:
            raise HTTPException(
                409,
                f"可用题目不足：排除最近 7 天已做题后仅有 {len(recommendations)} 道，至少需要 6 道",
            )
        return recommendations

    async def get_or_create_today(self, db: AsyncSession, user_id: int) -> DailyTask:
        today = datetime.now(CHINA_TIMEZONE).date()
        existing = await self._load_task(db, user_id, today)
        if existing:
            return existing

        recommendations = await self.recommend_today(db, user_id)
        max_day = await db.scalar(
            select(func.max(DailyTask.day_number)).where(DailyTask.user_id == user_id)
        )
        day_number = min((max_day or 0) + 1, 27)
        task = DailyTask(
            user_id=user_id,
            task_date=today,
            day_number=day_number,
            recommendation_version="rules-v1",
            items=[
                DailyTaskItem(
                    position=position,
                    question=recommendation.question,
                    recommendation_reason=recommendation.reason,
                )
                for position, recommendation in enumerate(recommendations, start=1)
            ],
        )
        db.add(task)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            existing = await self._load_task(db, user_id, today)
            if existing:
                return existing
            raise
        return await self._load_task(db, user_id, today)  # type: ignore[return-value]

    async def _load_task(self, db: AsyncSession, user_id: int, task_date: date) -> DailyTask | None:
        return await db.scalar(
            select(DailyTask)
            .where(DailyTask.user_id == user_id, DailyTask.task_date == task_date)
            .options(selectinload(DailyTask.items).selectinload(DailyTaskItem.question))
        )


daily_task_generator = DailyTaskGenerator()
