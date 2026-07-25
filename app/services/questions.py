from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question, QuestionType
from app.schemas.question import QuestionCreate, QuestionUpdate


async def get_question(db: AsyncSession, question_id: int, active_only: bool = True) -> Question:
    query = select(Question).where(Question.id == question_id)
    if active_only:
        query = query.where(Question.is_active.is_(True))
    question = await db.scalar(query)
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
    return question


async def list_questions(
    db: AsyncSession,
    page: int,
    page_size: int,
    question_type: QuestionType | None = None,
    difficulty: int | None = None,
) -> tuple[list[Question], int]:
    filters = [Question.is_active.is_(True)]
    if question_type:
        filters.append(Question.question_type == question_type)
    if difficulty:
        filters.append(Question.difficulty == difficulty)
    total = await db.scalar(select(func.count(Question.id)).where(*filters)) or 0
    result = await db.scalars(
        select(Question)
        .where(*filters)
        .order_by(Question.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(result), total


async def create_question(db: AsyncSession, data: QuestionCreate) -> Question:
    question = Question(**data.model_dump())
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


async def update_question(db: AsyncSession, question: Question, data: QuestionUpdate) -> Question:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(question, field, value)
    await db.commit()
    await db.refresh(question)
    return question


async def delete_question(db: AsyncSession, question: Question) -> None:
    question.is_active = False
    await db.commit()
