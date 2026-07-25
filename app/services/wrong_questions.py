from fastapi import HTTPException
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_point import KnowledgePoint, QuestionKnowledgePoint
from app.models.question import Question
from app.models.student_answer import StudentAnswer
from app.models.training_session import TrainingSession, TrainingType
from app.schemas.wrong_question import WrongQuestionRead, WrongQuestionSort
from app.services.training_sessions import TrainingItemSelection, create_session


def build_wrong_questions_query(
    user_id: int,
    *,
    subject: str | None = None,
    knowledge_point_code: str | None = None,
) -> Select:
    ranked_answers = (
        select(
            StudentAnswer.id.label("answer_id"),
            StudentAnswer.question_id,
            StudentAnswer.submitted_answer,
            StudentAnswer.analysis_status,
            StudentAnswer.ai_analysis,
            StudentAnswer.created_at.label("last_wrong_at"),
            func.count(StudentAnswer.id)
            .over(partition_by=StudentAnswer.question_id)
            .label("error_count"),
            func.row_number()
            .over(
                partition_by=StudentAnswer.question_id,
                order_by=(StudentAnswer.created_at.desc(), StudentAnswer.id.desc()),
            )
            .label("row_number"),
        )
        .where(
            StudentAnswer.user_id == user_id,
            StudentAnswer.is_correct.is_(False),
        )
        .subquery("ranked_wrong_answers")
    )
    statement = (
        select(
            ranked_answers.c.answer_id,
            Question.id.label("question_id"),
            Question.title,
            Question.content,
            Question.question_type,
            Question.options,
            Question.subject,
            Question.chapter,
            KnowledgePoint.code.label("knowledge_point_code"),
            KnowledgePoint.name.label("knowledge_point_name"),
            Question.difficulty,
            ranked_answers.c.submitted_answer,
            Question.correct_answer,
            Question.explanation,
            ranked_answers.c.analysis_status,
            ranked_answers.c.ai_analysis,
            ranked_answers.c.last_wrong_at,
            ranked_answers.c.error_count,
        )
        .join(Question, Question.id == ranked_answers.c.question_id)
        .join(
            QuestionKnowledgePoint,
            (QuestionKnowledgePoint.question_id == Question.id)
            & (QuestionKnowledgePoint.role == "primary"),
        )
        .join(
            KnowledgePoint,
            KnowledgePoint.id == QuestionKnowledgePoint.knowledge_point_id,
        )
        .where(ranked_answers.c.row_number == 1)
    )
    if subject:
        statement = statement.where(Question.subject == subject)
    if knowledge_point_code:
        statement = statement.where(KnowledgePoint.code == knowledge_point_code)
    return statement


async def list_wrong_questions(
    db: AsyncSession,
    user_id: int,
    *,
    subject: str | None,
    knowledge_point_code: str | None,
    sort: WrongQuestionSort,
    page: int,
    page_size: int,
) -> tuple[list[WrongQuestionRead], int]:
    statement = build_wrong_questions_query(
        user_id,
        subject=subject,
        knowledge_point_code=knowledge_point_code,
    )
    total = int(
        await db.scalar(
            select(func.count()).select_from(statement.order_by(None).subquery())
        )
        or 0
    )
    if sort == WrongQuestionSort.recent_desc:
        statement = statement.order_by(
            statement.selected_columns.last_wrong_at.desc(),
            statement.selected_columns.error_count.desc(),
            statement.selected_columns.question_id,
        )
    else:
        statement = statement.order_by(
            statement.selected_columns.error_count.desc(),
            statement.selected_columns.last_wrong_at.desc(),
            statement.selected_columns.question_id,
        )
    rows = (
        await db.execute(
            statement.offset((page - 1) * page_size).limit(page_size)
        )
    ).mappings()
    return [WrongQuestionRead.model_validate(row) for row in rows], total


async def create_wrong_review(
    db: AsyncSession,
    user_id: int,
    question_id: int,
) -> TrainingSession:
    latest_wrong = await db.scalar(
        select(StudentAnswer)
        .where(
            StudentAnswer.user_id == user_id,
            StudentAnswer.question_id == question_id,
            StudentAnswer.is_correct.is_(False),
        )
        .order_by(StudentAnswer.created_at.desc(), StudentAnswer.id.desc())
        .limit(1)
    )
    if not latest_wrong:
        raise HTTPException(404, "该题不在你的错题本中")
    question = await db.scalar(
        select(Question).where(
            Question.id == question_id,
            Question.is_active.is_(True),
        )
    )
    if not question:
        raise HTTPException(409, "该题当前不可用于训练")
    return await create_session(
        db,
        user_id,
        training_type=TrainingType.wrong_review,
        title=f"错题重练 · {question.title}",
        selections=[
            TrainingItemSelection(
                question_id=question.id,
                recommendation_reason=f"历史错题重练：{question.title}",
                source_answer_id=latest_wrong.id,
            )
        ],
        selection_version="wrong-review-v1",
        selection_config={
            "source": "wrong_question_book",
            "source_answer_id": latest_wrong.id,
        },
        subject=question.subject,
        chapter=question.chapter,
        knowledge_point=(question.knowledge_points[0] if question.knowledge_points else None),
    )
