from fastapi import APIRouter, Query, status

from app.api.dependencies import CurrentUser, DbSession
from app.models.question import QuestionType
from app.schemas.common import Message, Page
from app.schemas.question import QuestionAdminRead, QuestionCreate, QuestionRead, QuestionUpdate
from app.services import questions as service

router = APIRouter(prefix="/questions", tags=["题库"])


@router.get("", response_model=Page[QuestionRead])
async def list_questions(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    question_type: QuestionType | None = None,
    difficulty: int | None = Query(None, ge=1, le=5),
) -> Page[QuestionRead]:
    items, total = await service.list_questions(db, page, page_size, question_type, difficulty)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/{question_id}", response_model=QuestionRead)
async def get_question(question_id: int, db: DbSession) -> QuestionRead:
    return await service.get_question(db, question_id)


@router.post("", response_model=QuestionAdminRead, status_code=status.HTTP_201_CREATED)
async def create_question(
    data: QuestionCreate, db: DbSession, _user: CurrentUser
) -> QuestionAdminRead:
    return await service.create_question(db, data)


@router.patch("/{question_id}", response_model=QuestionAdminRead)
async def update_question(
    question_id: int, data: QuestionUpdate, db: DbSession, _user: CurrentUser
) -> QuestionAdminRead:
    question = await service.get_question(db, question_id, active_only=False)
    return await service.update_question(db, question, data)


@router.delete("/{question_id}", response_model=Message)
async def delete_question(question_id: int, db: DbSession, _user: CurrentUser) -> Message:
    question = await service.get_question(db, question_id, active_only=False)
    await service.delete_question(db, question)
    return Message(message="题目已停用")
