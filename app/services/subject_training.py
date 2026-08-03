from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_point import KnowledgePoint, QuestionKnowledgePoint
from app.models.knowledge_status import KnowledgeStatus
from app.models.question import Question, QuestionType
from app.models.student_answer import StudentAnswer
from app.models.training_session import TrainingSession, TrainingType
from app.schemas.training_session import (
    SubjectTrainingCatalog,
    SubjectTrainingChapter,
    SubjectTrainingCreate,
    SubjectTrainingKnowledgePoint,
    SubjectTrainingSubject,
)
from app.services.training_sessions import TrainingItemSelection, create_session

SELECTION_VERSION = "subject-v2"
FILL_SELECTION_VERSION = "fill-v1"
RECENT_DAYS = 7


@dataclass(frozen=True)
class QuestionSignals:
    mastery: float
    recent_wrong: bool
    recently_answered: bool


@dataclass
class CatalogBucket:
    question_ids: set[int]
    difficulties: Counter[int]


def _new_bucket() -> CatalogBucket:
    return CatalogBucket(question_ids=set(), difficulties=Counter())


def _difficulty_counts(counter: Counter[int]) -> dict[int, int]:
    return {level: counter[level] for level in range(1, 6)}


async def get_catalog(
    db: AsyncSession,
    *,
    question_type: QuestionType | None = None,
) -> SubjectTrainingCatalog:
    statement = (
        select(
            Question.id,
            Question.subject,
            Question.chapter,
            Question.difficulty,
            KnowledgePoint.code,
            KnowledgePoint.name,
        )
        .join(
            QuestionKnowledgePoint,
            (QuestionKnowledgePoint.question_id == Question.id)
            & (QuestionKnowledgePoint.role == "primary"),
        )
        .join(
            KnowledgePoint,
            KnowledgePoint.id == QuestionKnowledgePoint.knowledge_point_id,
        )
        .where(
            Question.is_active.is_(True),
            KnowledgePoint.is_active.is_(True),
            KnowledgePoint.level == 3,
            Question.subject == KnowledgePoint.subject,
        )
        .order_by(Question.subject, Question.chapter, KnowledgePoint.code, Question.id)
    )
    if question_type is not None:
        statement = statement.where(Question.question_type == question_type)
    rows = (await db.execute(statement)).all()
    subject_buckets: dict[str, CatalogBucket] = defaultdict(_new_bucket)
    chapter_buckets: dict[tuple[str, str], CatalogBucket] = defaultdict(_new_bucket)
    point_buckets: dict[tuple[str, str, str], CatalogBucket] = defaultdict(_new_bucket)
    point_names: dict[str, str] = {}
    for row in rows:
        chapter = row.chapter or "其他"
        point_names[row.code] = row.name
        for bucket in (
            subject_buckets[row.subject],
            chapter_buckets[(row.subject, chapter)],
            point_buckets[(row.subject, chapter, row.code)],
        ):
            bucket.question_ids.add(row.id)
            bucket.difficulties[row.difficulty] += 1

    subjects: list[SubjectTrainingSubject] = []
    for subject_name in sorted(subject_buckets):
        chapter_items: list[SubjectTrainingChapter] = []
        chapter_names = sorted(
            chapter
            for current_subject, chapter in chapter_buckets
            if current_subject == subject_name
        )
        for chapter_name in chapter_names:
            chapter_bucket = chapter_buckets[(subject_name, chapter_name)]
            point_codes = sorted(
                code
                for current_subject, current_chapter, code in point_buckets
                if current_subject == subject_name and current_chapter == chapter_name
            )
            chapter_items.append(
                SubjectTrainingChapter(
                    name=chapter_name,
                    question_count=len(chapter_bucket.question_ids),
                    difficulty_counts=_difficulty_counts(chapter_bucket.difficulties),
                    knowledge_points=[
                        SubjectTrainingKnowledgePoint(
                            code=code,
                            name=point_names[code],
                            question_count=len(
                                point_buckets[(subject_name, chapter_name, code)].question_ids
                            ),
                            difficulty_counts=_difficulty_counts(
                                point_buckets[
                                    (subject_name, chapter_name, code)
                                ].difficulties
                            ),
                        )
                        for code in point_codes
                    ],
                )
            )
        subject_bucket = subject_buckets[subject_name]
        subjects.append(
            SubjectTrainingSubject(
                name=subject_name,
                question_count=len(subject_bucket.question_ids),
                difficulty_counts=_difficulty_counts(subject_bucket.difficulties),
                chapters=chapter_items,
            )
        )
    return SubjectTrainingCatalog(subjects=subjects)


def _matches(question: Question, data: SubjectTrainingCreate) -> bool:
    if question.subject != data.subject:
        return False
    if data.chapter and (question.chapter or "其他") != data.chapter:
        return False
    return not data.knowledge_point or data.knowledge_point in question.knowledge_points


def _target_difficulty(mastery: float, recent_wrong: bool) -> int:
    if recent_wrong or mastery < 40:
        return 2
    if mastery >= 80:
        return 4
    return 3


async def create_subject_training(
    db: AsyncSession,
    user_id: int,
    data: SubjectTrainingCreate,
    *,
    question_type: QuestionType | None = None,
) -> TrainingSession:
    candidate_query = (
        select(Question, KnowledgePoint)
        .join(
            QuestionKnowledgePoint,
            (QuestionKnowledgePoint.question_id == Question.id)
            & (QuestionKnowledgePoint.role == "primary"),
        )
        .join(
            KnowledgePoint,
            KnowledgePoint.id == QuestionKnowledgePoint.knowledge_point_id,
        )
        .where(
            Question.is_active.is_(True),
            Question.subject == data.subject,
            KnowledgePoint.is_active.is_(True),
            KnowledgePoint.level == 3,
            KnowledgePoint.subject == Question.subject,
        )
    )
    if question_type is not None:
        candidate_query = candidate_query.where(Question.question_type == question_type)
    if data.chapter:
        candidate_query = candidate_query.where(Question.chapter == data.chapter)
    if data.knowledge_point_code:
        candidate_query = candidate_query.where(
            KnowledgePoint.code == data.knowledge_point_code
        )
    elif data.knowledge_point:
        candidate_query = candidate_query.where(
            KnowledgePoint.name == data.knowledge_point
        )
    if data.difficulty is not None:
        candidate_query = candidate_query.where(Question.difficulty == data.difficulty)
    candidate_rows = (
        await db.execute(candidate_query.order_by(Question.id))
    ).all()
    candidates = [row[0] for row in candidate_rows]
    point_by_question = {row[0].id: row[1] for row in candidate_rows}
    if len(candidates) < data.question_count:
        raise HTTPException(
            409,
            f"当前范围只有 {len(candidates)} 道可用题目，请减少题量或扩大训练范围",
        )

    mastery_rows = list(
        await db.scalars(
            select(KnowledgeStatus).where(
                KnowledgeStatus.user_id == user_id,
                KnowledgeStatus.subject == data.subject,
            )
        )
    )
    mastery_by_id = {
        row.knowledge_point_id: row.mastery_score
        for row in mastery_rows
        if row.knowledge_point_id is not None
    }
    mastery_by_name = {row.knowledge_point: row.mastery_score for row in mastery_rows}
    recent_since = datetime.now(UTC) - timedelta(days=RECENT_DAYS)
    recent_rows = (
        await db.execute(
            select(StudentAnswer.question_id, StudentAnswer.is_correct)
            .join(Question, Question.id == StudentAnswer.question_id)
            .where(
                StudentAnswer.user_id == user_id,
                Question.subject == data.subject,
                StudentAnswer.created_at >= recent_since,
            )
        )
    ).all()
    recently_answered = {question_id for question_id, _ in recent_rows}
    recently_wrong = {question_id for question_id, correct in recent_rows if not correct}

    def signals(question: Question) -> QuestionSignals:
        point = point_by_question[question.id]
        mastery = mastery_by_id.get(
            point.id,
            mastery_by_name.get(point.name, 50),
        )
        return QuestionSignals(
            mastery=mastery,
            recent_wrong=question.id in recently_wrong,
            recently_answered=question.id in recently_answered,
        )

    def rank(question: Question) -> tuple[int, float, int, int]:
        state = signals(question)
        target = _target_difficulty(state.mastery, state.recent_wrong)
        return (
            int(state.recently_answered),
            state.mastery,
            abs(question.difficulty - target),
            question.id,
        )

    selected = sorted(candidates, key=rank)[: data.question_count]
    selected_point_name = (
        point_by_question[candidates[0].id].name
        if candidates and (data.knowledge_point_code or data.knowledge_point)
        else None
    )
    detail = selected_point_name or data.chapter
    is_fill = question_type == QuestionType.fill_blank
    selections = [
        TrainingItemSelection(
            question_id=question.id,
            recommendation_reason=(
                "近期错题对应知识点强化"
                if signals(question).recent_wrong
                else f"匹配当前掌握度与难度 {question.difficulty}"
            ),
        )
        for question in selected
    ]
    return await create_session(
        db,
        user_id,
        training_type=(TrainingType.fill_review if is_fill else TrainingType.subject),
        title=(
            f"概念记忆 · {data.subject}"
            if is_fill
            else f"{data.subject} · {detail or '综合专项'}"
        ),
        selections=selections,
        selection_version=(FILL_SELECTION_VERSION if is_fill else SELECTION_VERSION),
        selection_config={
            "question_count": data.question_count,
            "recent_exclusion_days": RECENT_DAYS,
            "algorithm": "rule_based",
            "knowledge_point_code": data.knowledge_point_code,
            "difficulty": data.difficulty,
            "question_type": question_type.value if question_type else None,
        },
        subject=data.subject,
        chapter=data.chapter,
        knowledge_point=selected_point_name or data.knowledge_point,
    )
